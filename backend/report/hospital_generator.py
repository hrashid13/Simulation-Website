"""
PDF report generator for HospitalSim.

Shares the structural approach of the ParkSim generator (flat story, cream-block
helpers, matplotlib figures embedded as images) but not its palette: the park's
brown/green fairground theme would be wrong on a clinical report, so this uses a
navy/white clinical treatment and a Helvetica face.

Matplotlib styling is applied through `plt.rc_context` rather than a global
`plt.rcParams.update`. The park generator mutates rcParams at import time, so a
second module doing the same would silently restyle whichever report was
generated second.
"""

import io

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor
from reportlab.lib.enums import TA_CENTER
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    Image as RLImage, KeepTogether,
)

# ---------------------------------------------------------------------------
# Layout
# ---------------------------------------------------------------------------
PAGE_W, PAGE_H = letter
MARGIN = 0.55 * inch
CONTENT_W = PAGE_W - 2 * MARGIN
CARD_PAD = 10
INNER_W = CONTENT_W - 2 * CARD_PAD

CHART_FULL_W = INNER_W / 72
CHART_HALF_W = ((INNER_W - 8) / 2) / 72
CHART_FULL_H = 2.7
CHART_HALF_H = 2.9

# ---------------------------------------------------------------------------
# Clinical palette
#
# Categorical department hues and the ESI ordinal ramp are the validated sets
# from the data-viz reference palette, checked against a white card surface:
#   categorical - worst adjacent CVD dE 24.2 (protan)
#   ESI ramp    - monotone lightness, single hue, light end 2.11:1
# Aqua and yellow fall below 3:1 on white, so every chart using them carries
# direct value labels or an accompanying table (the relief rule).
# ---------------------------------------------------------------------------
NAVY        = HexColor("#0f2f4f")
NAVY_LIGHT  = HexColor("#1d4b78")
PAGE_PLANE  = HexColor("#eef2f6")
CARD        = HexColor("#ffffff")
CARD_ALT    = HexColor("#f3f6f9")
INK         = HexColor("#0b0b0b")
INK_SOFT    = HexColor("#52514e")
RULE        = HexColor("#c3c2b7")
WHITE       = HexColor("#ffffff")

DEPT_HEX = {
    "emergency_room":    "#2a78d6",
    "radiology_lab":     "#1baf7a",
    "surgery":           "#eda100",
    "icu":               "#008300",
    "general_ward":      "#4a3aa7",
    "outpatient_clinic": "#e34948",
}

# ESI 1 (most severe) darkest through ESI 5 lightest.
ESI_HEX = {1: "#0d366b", 2: "#1c5cab", 3: "#2a78d6", 4: "#5598e7", 5: "#86b6ef"}

REVENUE_HEX = "#2a78d6"
COST_HEX    = "#eb6834"

STATUS_GOOD     = "#0ca30c"
STATUS_WARNING  = "#fab219"
STATUS_CRITICAL = "#d03b3b"

_INK_HEX  = "#0b0b0b"
_MUTED    = "#898781"
_GRID_HEX = "#e1e0d9"

# Scoped so the ParkSim generator's global rcParams are never disturbed.
_RC = {
    "font.family":      "sans-serif",
    "font.sans-serif":  ["DejaVu Sans"],
    "font.size":        8,
    "axes.facecolor":   "#ffffff",
    "figure.facecolor": "#ffffff",
    "axes.edgecolor":   _GRID_HEX,
    "axes.linewidth":   1.0,
    "grid.color":       _GRID_HEX,
    "grid.linewidth":   0.8,
    "text.color":       _INK_HEX,
    "axes.labelcolor":  _INK_HEX,
    "xtick.color":      _MUTED,
    "ytick.color":      _MUTED,
    "legend.frameon":   False,
}

# ---------------------------------------------------------------------------
# Paragraph styles
# ---------------------------------------------------------------------------
H1_STYLE = ParagraphStyle("H1", fontName="Helvetica-Bold", fontSize=15,
                          textColor=WHITE, alignment=TA_CENTER, leading=19)
SUB_STYLE = ParagraphStyle("Sub", fontName="Helvetica", fontSize=9.5,
                           textColor=HexColor("#b9cbdd"), alignment=TA_CENTER, leading=13)
H2_STYLE = ParagraphStyle("H2", fontName="Helvetica-Bold", fontSize=9.5,
                          textColor=WHITE, leading=13)
NOTE_STYLE = ParagraphStyle("Note", fontName="Helvetica-Oblique", fontSize=7,
                            textColor=INK_SOFT, leading=9.5)
BODY_STYLE = ParagraphStyle("Body", fontName="Helvetica", fontSize=8,
                            textColor=INK, leading=11)


def _page_bg(canvas, doc):
    canvas.saveState()
    canvas.setFillColor(PAGE_PLANE)
    canvas.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)
    canvas.setFillColor(NAVY)
    canvas.rect(0, PAGE_H - 8, PAGE_W, 8, fill=1, stroke=0)
    canvas.setFont("Helvetica", 7)
    canvas.setFillColor(HexColor("#6b7783"))
    canvas.drawRightString(PAGE_W - MARGIN, MARGIN * 0.55, f"Page {doc.page}")
    canvas.drawString(MARGIN, MARGIN * 0.55, "HospitalSim — Simuleras")
    canvas.restoreState()


# ---------------------------------------------------------------------------
# Building blocks
# ---------------------------------------------------------------------------

def _title_flowable(title):
    t = Table([[Paragraph(title, H2_STYLE)]], colWidths=[CONTENT_W])
    t.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), NAVY),
        ("TOPPADDING",    (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ("LEFTPADDING",   (0, 0), (-1, -1), 11),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 11),
    ]))
    return t


def _card_flowable(items):
    """
    White card for fixed-height content. Never put a splittable table here.

    Vertical padding is applied only to the outer edges. Setting it on every row
    charged 20pt per item, which cost the summary card 2.5 inches of dead space
    and pushed later sections into splitting across pages.
    """
    t = Table([[i] for i in items], colWidths=[CONTENT_W])
    t.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), CARD),
        ("LINEBELOW",     (0, -1), (-1, -1), 1, RULE),
        ("LINEBEFORE",    (0, 0), (0, -1), 1, RULE),
        ("LINEAFTER",     (-1, 0), (-1, -1), 1, RULE),
        ("TOPPADDING",    (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING",    (0, 0), (-1, 0), CARD_PAD),
        ("BOTTOMPADDING", (0, -1), (-1, -1), CARD_PAD),
        ("LEFTPADDING",   (0, 0), (-1, -1), CARD_PAD),
        ("RIGHTPADDING",  (0, 0), (-1, -1), CARD_PAD),
        ("VALIGN",        (0, 0), (-1, -1), "TOP"),
    ]))
    return t


def _section(title, items, story):
    """
    Emit a heading and its card as one unit.

    KeepTogether moves a section wholly to the next page rather than letting the
    card split: a split card renders with an open bottom edge and stranded its
    table on an otherwise empty page.
    """
    story.append(KeepTogether([_title_flowable(title), _card_flowable(items)]))
    story.append(Spacer(1, 12))


def _section_end(story):
    story.append(Spacer(1, 12))


def _data_table(rows, col_widths=None, align_left_first=False):
    cmds = [
        ("BACKGROUND",    (0, 0), (-1, 0),  NAVY_LIGHT),
        ("TEXTCOLOR",     (0, 0), (-1, 0),  WHITE),
        ("FONTNAME",      (0, 0), (-1, 0),  "Helvetica-Bold"),
        ("FONTNAME",      (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE",      (0, 0), (-1, -1), 7.5),
        ("ALIGN",         (0, 0), (-1, -1), "CENTER"),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ("GRID",          (0, 0), (-1, -1), 0.5, RULE),
        ("TOPPADDING",    (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]
    if align_left_first:
        cmds.append(("ALIGN", (0, 1), (0, -1), "LEFT"))
        cmds.append(("LEFTPADDING", (0, 0), (0, -1), 7))
    for i in range(1, len(rows)):
        if i % 2 == 0:
            cmds.append(("BACKGROUND", (0, i), (-1, i), CARD_ALT))
    t = Table(rows, colWidths=col_widths, repeatRows=1)
    t.setStyle(TableStyle(cmds))
    return t


def _fig(fig, w, h):
    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight", dpi=150)
    plt.close(fig)
    buf.seek(0)
    return RLImage(buf, width=w * inch, height=h * inch)


def _clean_axes(ax):
    ax.grid(axis="y", alpha=0.7, linewidth=0.7)
    ax.set_axisbelow(True)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)


def _money(v):     return f"-${abs(v):,.0f}" if v < 0 else f"${v:,.0f}"
def _money_c(v):   return f"-${abs(v):,.2f}" if v < 0 else f"${v:,.2f}"
def _int(v):       return f"{v:,}"
def _pct(v):       return f"{v:.1f}%"
def _mins(v):      return f"{v:,.0f}m"


def _hours(minutes):
    return f"{minutes / 60:.1f}h" if minutes >= 90 else f"{minutes:.0f}m"


def _money_axis(v, _pos=None):
    if v == 0:
        return "$0"
    if abs(v) >= 1e6:
        return f"${v / 1e6:.0f}M"
    return f"${v / 1e3:.0f}K"


# ---------------------------------------------------------------------------
# Sections
# ---------------------------------------------------------------------------

def _section_summary(story, data):
    s = data["summary"]

    kpi_top = _data_table([
        ["Period", "Patients", "Admissions", "Discharges", "Transfers", "Diverted"],
        [f"{s['total_days']} days", _int(s["total_patients"]), _int(s["total_admissions"]),
         _int(s["total_discharges"]), _int(s["total_transfers"]), _int(s["total_diversions"])],
    ], col_widths=[INNER_W / 6] * 6)

    kpi_mid = _data_table([
        ["Mean ER Wait", "Longest ER Wait", "Readmission Rate",
         "Complication Rate", "Satisfaction", "Operating Margin"],
        [_hours(s["avg_er_wait_minutes"]), _hours(s["max_er_wait_minutes"]),
         _pct(s["readmission_rate_pct"]), _pct(s["complication_rate_pct"]),
         f"{s['avg_satisfaction']}/100", _pct(s["net_margin_pct"])],
    ], col_widths=[INNER_W / 6] * 6)

    fin = _data_table([
        ["Total Revenue", "Total Cost", "Net Margin"],
        [_money(s["total_revenue"]), _money(s["total_cost"]), _money(s["net_margin"])],
    ], col_widths=[INNER_W / 3] * 3)

    bd, wd = s["busiest_day"], s["worst_day"]
    days_tbl = _data_table([
        ["", "Day", "Day of Week", "Event", "Arrivals", "Mean ER Wait", "Diverted"],
        ["BUSIEST", str(bd["day"]), bd["day_of_week"], bd["event"],
         _int(bd["arrivals"]), "—", "—"],
        ["WORST", str(wd["day"]), wd["day_of_week"], wd["event"],
         _int(wd["arrivals"]), _hours(wd["avg_er_wait_minutes"]), _int(wd["diversions"])],
    ], col_widths=[INNER_W * 0.11, INNER_W * 0.07, INNER_W * 0.16, INNER_W * 0.20,
                   INNER_W * 0.13, INNER_W * 0.19, INNER_W * 0.14])

    note = Paragraph(
        "Worst day is ranked by mean emergency department wait, then by diversions. "
        "Readmission rate is measured at discharge, so it is independent of run length.",
        NOTE_STYLE)

    _section("Section 1: Executive Summary", [kpi_top, Spacer(1, 5), kpi_mid, Spacer(1, 5), fin,
           Spacer(1, 7), days_tbl, Spacer(1, 5), note], story)


def _section_patient_flow(story, data):
    daily = data["daily_data"]
    days = [d["day"] for d in daily]

    with plt.rc_context(_RC):
        fig, ax = plt.subplots(figsize=(CHART_FULL_W, CHART_FULL_H))
        ax.plot(days, [d["arrivals"] for d in daily], color=DEPT_HEX["emergency_room"],
                linewidth=2, label="Arrivals")
        ax.plot(days, [d["discharges"] for d in daily], color=DEPT_HEX["radiology_lab"],
                linewidth=2, label="Discharges")
        ax.plot(days, [d["admissions"] for d in daily], color=DEPT_HEX["general_ward"],
                linewidth=2, label="Inpatient admissions")
        ax.set_xlabel("Day")
        ax.set_ylabel("Patients")
        ax.set_title("Daily patient throughput", fontweight="bold", loc="left")
        ax.legend(fontsize=7, loc="upper right", ncol=3)
        _clean_axes(ax)
        flow_img = _fig(fig, CHART_FULL_W, CHART_FULL_H)

    total_days = len(daily) or 1
    avg = lambda k: sum(d[k] for d in daily) / total_days
    tbl = _data_table([
        ["", "Arrivals", "Inpatient Admissions", "Discharges", "Transfers", "Diverted"],
        ["Total", _int(sum(d["arrivals"] for d in daily)),
         _int(sum(d["admissions"] for d in daily)),
         _int(sum(d["discharges"] for d in daily)),
         _int(sum(d["transfers"] for d in daily)),
         _int(sum(d["diversions"] for d in daily))],
        ["Daily mean", f"{avg('arrivals'):.1f}", f"{avg('admissions'):.1f}",
         f"{avg('discharges'):.1f}", f"{avg('transfers'):.1f}", f"{avg('diversions'):.2f}"],
    ], col_widths=[INNER_W * 0.16] + [INNER_W * 0.168] * 5, align_left_first=True)

    _section("Section 2: Patient Flow and Throughput", [flow_img, Spacer(1, 7), tbl], story)


def _section_occupancy(story, data):
    series = data["occupancy_series"]
    hourly = data["summary"]["occupancy_resolution"] == "hourly"
    stats = data["department_stats"]

    if hourly:
        x = [row["day"] + row["hour"] / 24.0 for row in series]
        xlabel = "Day"
    else:
        x = [row["day"] for row in series]
        xlabel = "Day"

    with plt.rc_context(_RC):
        fig, ax = plt.subplots(figsize=(CHART_FULL_W, CHART_FULL_H))
        for key, hex_color in DEPT_HEX.items():
            ax.plot(x, [row[key] for row in series], color=hex_color,
                    linewidth=1.6, label=stats[key]["name"])
        ax.set_xlabel(xlabel)
        ax.set_ylabel("Occupancy (%)")
        ax.set_ylim(0, 105)
        title = "Bed occupancy" + (" (hourly)" if hourly else " (daily mean)")
        ax.set_title(title, fontweight="bold", loc="left")
        ax.legend(fontsize=6.5, loc="upper center", ncol=6, bbox_to_anchor=(0.5, -0.18))
        _clean_axes(ax)
        occ_img = _fig(fig, CHART_FULL_W, CHART_FULL_H)

    rows = [["Department", "Capacity", "Mean Occ.", "Peak Occ.", "Encounters", "Bed Hours"]]
    for key, st in stats.items():
        rows.append([st["name"], f"{st['capacity']} {st['unit']}",
                     _pct(st["avg_occupancy_pct"]), _pct(st["peak_occupancy_pct"]),
                     _int(st["total_encounters"]), _int(int(st["total_bed_hours"]))])

    tbl = _data_table(rows, col_widths=[INNER_W * 0.24, INNER_W * 0.18, INNER_W * 0.13,
                                        INNER_W * 0.13, INNER_W * 0.16, INNER_W * 0.16],
                      align_left_first=True)

    _section("Section 3: Department Occupancy", [occ_img, Spacer(1, 7), tbl], story)


def _section_waits_triage(story, data):
    stats = data["department_stats"]
    esi = data["esi_stats"]

    queued = [(k, v) for k, v in stats.items() if v["queue_reported"]]

    with plt.rc_context(_RC):
        fig, ax = plt.subplots(figsize=(CHART_HALF_W, CHART_HALF_H))
        names = [v["name"] for _, v in queued]
        vals = [v["avg_wait_minutes"] for _, v in queued]
        colors = [DEPT_HEX[k] for k, _ in queued]
        bars = ax.barh(names, vals, color=colors, height=0.62)
        # Direct labels: aqua and yellow fall below 3:1 on white, so the value
        # must not rely on the fill colour being legible.
        for bar, val in zip(bars, vals):
            ax.text(bar.get_width() + max(vals) * 0.02, bar.get_y() + bar.get_height() / 2,
                    _hours(val), va="center", fontsize=7, color=_INK_HEX)
        ax.set_xlabel("Mean wait for a bed (minutes)")
        ax.set_title("Wait by department", fontweight="bold", loc="left")
        ax.set_xlim(0, max(vals) * 1.22 if max(vals) else 1)
        ax.invert_yaxis()
        ax.grid(axis="x", alpha=0.7, linewidth=0.7)
        ax.set_axisbelow(True)
        for side in ("top", "right"):
            ax.spines[side].set_visible(False)
        wait_img = _fig(fig, CHART_HALF_W, CHART_HALF_H)

        fig, ax = plt.subplots(figsize=(CHART_HALF_W, CHART_HALF_H))
        levels = sorted(esi, key=int)
        labels = [f"ESI {l}\n{esi[l]['label']}" for l in levels]
        counts = [esi[l]["count"] for l in levels]
        bars = ax.barh(labels, counts, color=[ESI_HEX[int(l)] for l in levels], height=0.62)
        for bar, l in zip(bars, levels):
            ax.text(bar.get_width() + max(counts) * 0.02, bar.get_y() + bar.get_height() / 2,
                    f"{esi[l]['share_pct']}%", va="center", fontsize=7, color=_INK_HEX)
        ax.set_xlabel("Patients triaged")
        ax.set_title("Triage severity mix", fontweight="bold", loc="left")
        ax.set_xlim(0, max(counts) * 1.20 if max(counts) else 1)
        ax.invert_yaxis()
        ax.tick_params(axis="y", labelsize=6.5)
        ax.grid(axis="x", alpha=0.7, linewidth=0.7)
        ax.set_axisbelow(True)
        for side in ("top", "right"):
            ax.spines[side].set_visible(False)
        esi_img = _fig(fig, CHART_HALF_W, CHART_HALF_H)

    charts = Table([[wait_img, esi_img]],
                   colWidths=[(INNER_W - 8) / 2 + 4, (INNER_W - 8) / 2 + 4])
    charts.setStyle(TableStyle([
        ("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0), ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))

    rows = [["ESI", "Severity", "Patients", "Share", "Mean ER Wait", "Target", "Within Target"]]
    for level in sorted(esi, key=int):
        e = esi[level]
        rows.append([str(level), e["label"], _int(e["count"]), _pct(e["share_pct"]),
                     _mins(e["avg_er_wait_minutes"]), f"{e['target_wait_minutes']}m",
                     _pct(e["within_target_pct"])])

    esi_tbl = _data_table(rows, col_widths=[INNER_W * 0.07, INNER_W * 0.20, INNER_W * 0.13,
                                            INNER_W * 0.11, INNER_W * 0.17, INNER_W * 0.12,
                                            INNER_W * 0.20])

    note = Paragraph(
        "Wait is time from arrival to occupying a bed. Departments other than the emergency "
        "department measure boarding time — the delay in transferring a patient who is already "
        "in the hospital. Time-to-provider targets are the standard ESI benchmarks.",
        NOTE_STYLE)

    _section("Section 4: Wait Times and Triage", [charts, Spacer(1, 6), esi_tbl, Spacer(1, 5), note], story)


def _section_capacity_strain(story, data):
    daily = data["daily_data"]
    stats = data["department_stats"]
    days = [d["day"] for d in daily]

    with plt.rc_context(_RC):
        fig, ax = plt.subplots(figsize=(CHART_FULL_W, CHART_FULL_H * 0.82))
        ax.bar(days, [d["diversions"] for d in daily], color=STATUS_CRITICAL,
               width=0.85 if len(days) < 90 else 1.0)
        ax.set_xlabel("Day")
        ax.set_ylabel("Patients diverted")
        ax.set_title("Diversions — arrivals turned away when full",
                     fontweight="bold", loc="left")
        # A count axis must not offer half a patient.
        ax.yaxis.set_major_locator(plt.MaxNLocator(integer=True))
        ax.set_xlim(0.5, len(days) + 0.5)
        _clean_axes(ax)
        div_img = _fig(fig, CHART_FULL_W, CHART_FULL_H * 0.82)

    rows = [["Department", "Staffed Level", "Staff Utilisation", "Disruptions",
             "Hours Lost", "Peak Occupancy"]]
    for key, st in stats.items():
        rows.append([st["name"], f"{st['staffed_level']}",
                     _pct(st["staff_utilization_pct"]), _int(st["disruption_count"]),
                     _int(st["disruption_hours"]), _pct(st["peak_occupancy_pct"])])

    tbl = _data_table(rows, col_widths=[INNER_W * 0.24, INNER_W * 0.15, INNER_W * 0.18,
                                        INNER_W * 0.13, INNER_W * 0.13, INNER_W * 0.17],
                      align_left_first=True)

    note = Paragraph(
        "Staff utilisation weights each patient by the staffing intensity of their archetype, "
        "so it can exceed 100%: the rostered level is fixed against bed capacity, while demand "
        "rises with case acuity. A figure above 100% means the department was understaffed for "
        "the mix it received, not that staff were double-booked.",
        NOTE_STYLE)

    _section("Section 5: Capacity Strain", [div_img, Spacer(1, 7), tbl, Spacer(1, 5), note], story)


def _section_financials(story, data):
    stats = data["department_stats"]
    s = data["summary"]

    with plt.rc_context(_RC):
        fig, ax = plt.subplots(figsize=(CHART_FULL_W, CHART_FULL_H))
        names = [v["name"] for v in stats.values()]
        revenue = [v["revenue"] for v in stats.values()]
        cost = [v["cost"] for v in stats.values()]
        idx = range(len(names))
        h = 0.36
        ax.barh([i + h / 2 for i in idx], revenue, height=h,
                color=REVENUE_HEX, label="Revenue")
        ax.barh([i - h / 2 for i in idx], cost, height=h,
                color=COST_HEX, label="Cost")
        ax.set_yticks(list(idx))
        ax.set_yticklabels(names, fontsize=7)
        ax.set_xlabel("US dollars")
        ax.set_title("Revenue against cost by department", fontweight="bold", loc="left")
        ax.legend(fontsize=7, loc="lower right", ncol=2)
        ax.invert_yaxis()
        ax.xaxis.set_major_formatter(plt.FuncFormatter(_money_axis))
        ax.grid(axis="x", alpha=0.7, linewidth=0.7)
        ax.set_axisbelow(True)
        for side in ("top", "right"):
            ax.spines[side].set_visible(False)
        fin_img = _fig(fig, CHART_FULL_W, CHART_FULL_H)

    rows = [["Department", "Encounters", "Revenue", "Cost", "Net"]]
    for st in stats.values():
        rows.append([st["name"], _int(st["total_encounters"]), _money(st["revenue"]),
                     _money(st["cost"]), _money(st["net_margin"])])
    for svc in data["service_stats"].values():
        rows.append([f"{svc['name']} (service)", _int(svc["total_transactions"]),
                     _money(svc["revenue"]), "—", _money(svc["revenue"])])
    rows.append(["TOTAL", "—", _money_c(s["total_revenue"]),
                 _money_c(s["total_cost"]), _money_c(s["net_margin"])])

    tbl = _data_table(rows, col_widths=[INNER_W * 0.30, INNER_W * 0.14, INNER_W * 0.19,
                                        INNER_W * 0.19, INNER_W * 0.18],
                      align_left_first=True)

    note = Paragraph(
        "Revenue is a flat per-encounter estimate with no payer or insurance modelling. Cost "
        "combines occupied bed hours with a rostered staffing cost fixed against capacity. "
        "Inpatient units running at a loss against procedural revenue is the expected shape, "
        "not an error.",
        NOTE_STYLE)

    _section("Section 6: Financial Performance", [fin_img, Spacer(1, 7), tbl, Spacer(1, 5), note], story)


def _section_events(story, data):
    summary = data["summary"]["event_summary"]

    rows = [["Event", "Days", "Mean Arrivals", "Mean Diversions", "Total Arrivals"]]
    for name, b in summary.items():
        rows.append([name, _int(b["count"]), f"{b['avg_arrivals']:.1f}",
                     f"{b['avg_diversions']:.2f}", _int(b["total_arrivals"])])

    tbl = _data_table(rows, col_widths=[INNER_W * 0.28, INNER_W * 0.12, INNER_W * 0.20,
                                        INNER_W * 0.20, INNER_W * 0.20],
                      align_left_first=True)

    note = Paragraph(
        "A seasonal surge raises volume while lowering average acuity. A staffing shortage "
        "leaves demand unchanged and cuts effective capacity instead. A mass casualty adds a "
        "burst of high-acuity arrivals within a single hour.",
        NOTE_STYLE)

    _section("Section 7: Event Impact", [tbl, Spacer(1, 5), note], story)


def _section_disruptions(story, data):
    disruptions = data["disruptions"]
    story.append(_title_flowable("Section 8: Disruption Log"))

    if not disruptions:
        story.append(_card_flowable(
            [Paragraph("No disruptions were recorded during this simulation.", BODY_STYLE)]))
    else:
        # Placed flat in the story so ReportLab can split it across pages.
        rows = [["Day", "Department", "Disruption", "Hours"]]
        rows += [[str(d["day"]), d["department"], d["type"], str(d["hours"])]
                 for d in disruptions]
        story.append(Spacer(1, 4))
        story.append(_data_table(
            rows,
            col_widths=[CONTENT_W * 0.10, CONTENT_W * 0.30,
                        CONTENT_W * 0.45, CONTENT_W * 0.15]))

    _section_end(story)


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def generate_hospital_pdf_report(data: dict) -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=letter,
        leftMargin=MARGIN, rightMargin=MARGIN,
        topMargin=MARGIN, bottomMargin=MARGIN,
        title="Hospital Simulation Report",
        author="Simuleras",
    )

    s = data["summary"]
    title_card = Table(
        [[Paragraph("HOSPITAL OPERATIONS SIMULATION REPORT", H1_STYLE)],
         [Paragraph(
             f"{s['total_days']}-day simulation &nbsp;·&nbsp; "
             f"{s['total_patients']:,} patients &nbsp;·&nbsp; "
             f"{s['avg_daily_arrivals']:.0f} arrivals per day",
             SUB_STYLE)]],
        colWidths=[CONTENT_W],
    )
    title_card.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), NAVY),
        ("TOPPADDING",    (0, 0), (-1, -1), 13),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 13),
        ("LEFTPADDING",   (0, 0), (-1, -1), 12),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 12),
    ]))

    story = [title_card, Spacer(1, 16)]

    # No manual page breaks: each section is a KeepTogether unit, so sections
    # pack onto a page until one does not fit and moves whole to the next.
    _section_summary(story, data)
    _section_patient_flow(story, data)
    _section_occupancy(story, data)
    _section_waits_triage(story, data)
    _section_capacity_strain(story, data)
    _section_financials(story, data)
    _section_events(story, data)
    _section_disruptions(story, data)

    doc.build(story, onFirstPage=_page_bg, onLaterPages=_page_bg)
    buf.seek(0)
    return buf.read()
