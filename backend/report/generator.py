import io
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.ticker as mticker

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor, white
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    Image as RLImage, PageBreak,
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT

# ---------------------------------------------------------------------------
# Layout constants
# ---------------------------------------------------------------------------
PAGE_W, PAGE_H = letter
MARGIN = 0.55 * inch
CONTENT_W = PAGE_W - 2 * MARGIN   # ~525 pt
CARD_PAD = 10                      # pt, padding inside card
INNER_W = CONTENT_W - 2 * CARD_PAD
HALF_W = (INNER_W - 8) / 2

CHART_FULL_W = INNER_W / 72       # inches for matplotlib
CHART_HALF_W = HALF_W / 72
CHART_FULL_H = 2.9
CHART_HALF_H = 3.1

# ---------------------------------------------------------------------------
# Palette — mirrors the website CSS variables
# ---------------------------------------------------------------------------
CREAM       = HexColor("#f5e6c8")
CREAM_DARK  = HexColor("#deca9a")
CREAM_LIGHT = HexColor("#fffaf0")
BROWN       = HexColor("#6b4c11")
BROWN_DARK  = HexColor("#3d2b00")
GREEN_L     = HexColor("#6aaa3a")
GREEN_D     = HexColor("#4a8228")
ORANGE      = HexColor("#e08a10")
BLUE_C      = HexColor("#2e7ab8")
RED_C       = HexColor("#d43030")

W_COLORS_HEX  = {"Sunny": "#F9A825", "Cloudy": "#90A4AE", "Rainy": "#42A5F5"}
REV_HEX       = ["#2e7ab8", "#2E7D32", "#e08a10"]
ARCH_HEX      = ["#EF5350", "#42A5F5", "#66BB6A", "#FFA726", "#AB47BC", "#26C6DA"]
RIDE_HEX      = "#5C6BC0"
FB_HEX        = "#2E7D32"
RETAIL_HEX    = "#e08a10"

# ---------------------------------------------------------------------------
# Matplotlib global style — cream background, brown text/axes
# ---------------------------------------------------------------------------
plt.rcParams.update({
    "font.family":       "monospace",
    "font.size":         8,
    "axes.facecolor":    "#fffaf0",
    "figure.facecolor":  "#f5e6c8",
    "axes.edgecolor":    "#6b4c11",
    "axes.linewidth":    1.5,
    "grid.color":        "#deca9a",
    "grid.linewidth":    1.0,
    "text.color":        "#3d2b00",
    "axes.labelcolor":   "#3d2b00",
    "xtick.color":       "#3d2b00",
    "ytick.color":       "#3d2b00",
})

# ---------------------------------------------------------------------------
# ReportLab styles
# ---------------------------------------------------------------------------
H1_STYLE = ParagraphStyle(
    "H1", fontName="Courier-Bold", fontSize=14,
    textColor=CREAM, alignment=TA_CENTER, spaceAfter=0,
)
H2_STYLE = ParagraphStyle(
    "H2", fontName="Courier-Bold", fontSize=9,
    textColor=CREAM, spaceAfter=0, leading=16,
)
BODY_STYLE = ParagraphStyle(
    "Body", fontName="Courier", fontSize=8,
    textColor=BROWN_DARK, spaceAfter=0,
)
SMALL_STYLE = ParagraphStyle(
    "Small", fontName="Courier", fontSize=7,
    textColor=BROWN, spaceAfter=0,
)
SUB_STYLE = ParagraphStyle(
    "Sub", fontName="Courier", fontSize=10,
    textColor=CREAM_DARK, alignment=TA_CENTER, spaceAfter=0,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _page_bg(canvas, doc):
    canvas.saveState()
    tile = 14
    canvas.setFillColor(GREEN_L)
    canvas.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)
    canvas.setFillColor(GREEN_D)
    for row in range(int(PAGE_H / tile) + 2):
        for col in range(int(PAGE_W / tile) + 2):
            if (row + col) % 2 == 0:
                canvas.rect(col * tile, row * tile, tile, tile, fill=1, stroke=0)
    canvas.restoreState()


def _card(title, inner_table, story):
    """Wraps a content table in a cream card with a dark-brown pixel header."""
    card = Table(
        [[Paragraph(title, H2_STYLE)], [inner_table]],
        colWidths=[CONTENT_W],
    )
    card.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, 0),  BROWN_DARK),
        ("BACKGROUND",    (0, 1), (-1, -1), CREAM),
        ("BOX",           (0, 0), (-1, -1), 3, BROWN),
        ("LINEBELOW",     (0, 0), (-1, 0),  2, BROWN),
        ("TOPPADDING",    (0, 0), (-1, 0),  8),
        ("BOTTOMPADDING", (0, 0), (-1, 0),  8),
        ("LEFTPADDING",   (0, 0), (-1, 0),  12),
        ("TOPPADDING",    (0, 1), (-1, -1), CARD_PAD),
        ("BOTTOMPADDING", (0, 1), (-1, -1), CARD_PAD),
        ("LEFTPADDING",   (0, 1), (-1, -1), CARD_PAD),
        ("RIGHTPADDING",  (0, 0), (-1, -1), CARD_PAD),
    ]))
    story.append(card)
    story.append(Spacer(1, 14))


def _data_table(rows, col_widths=None):
    n = len(rows)
    cmds = [
        ("BACKGROUND",    (0, 0), (-1, 0),  BROWN_DARK),
        ("TEXTCOLOR",     (0, 0), (-1, 0),  CREAM),
        ("FONTNAME",      (0, 0), (-1, 0),  "Courier-Bold"),
        ("FONTNAME",      (0, 1), (-1, -1), "Courier"),
        ("FONTSIZE",      (0, 0), (-1, -1), 8),
        ("ALIGN",         (0, 0), (-1, -1), "CENTER"),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ("BOX",           (0, 0), (-1, -1), 2, BROWN),
        ("GRID",          (0, 0), (-1, -1), 1, BROWN),
        ("TOPPADDING",    (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]
    for i in range(1, n):
        bg = CREAM_DARK if i % 2 == 0 else CREAM
        cmds.append(("BACKGROUND", (0, i), (-1, i), bg))
    t = Table(rows, colWidths=col_widths)
    t.setStyle(TableStyle(cmds))
    return t


def _fig(fig, w, h):
    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight", dpi=150)
    plt.close(fig)
    buf.seek(0)
    return RLImage(buf, width=w * inch, height=h * inch)


def _inner(rows, col_widths=None):
    """Plain table for card content layout — no visible borders, cream bg."""
    t = Table(rows, colWidths=col_widths)
    t.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), CREAM),
        ("TOPPADDING",    (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING",   (0, 0), (-1, -1), 0),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 0),
        ("VALIGN",        (0, 0), (-1, -1), "TOP"),
    ]))
    return t


def _fmt_money(v): return f"${v:,.2f}"
def _fmt_int(v):   return f"{v:,}"

DOW_ORDER = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

# ---------------------------------------------------------------------------
# Section builders
# ---------------------------------------------------------------------------

def _section_summary(story, data):
    s = data["summary"]
    kpi = _data_table(
        [
            ["Period", "Total Attendance", "Total Revenue",
             "Ticket Rev", "Food & Bev Rev", "Retail Rev"],
            [
                f"{s['total_days']} days",
                _fmt_int(s["total_attendance"]),
                _fmt_money(s["total_revenue"]),
                _fmt_money(s["total_ticket_revenue"]),
                _fmt_money(s["total_food_beverage_revenue"]),
                _fmt_money(s["total_retail_merchandise_revenue"]),
            ],
        ],
        col_widths=[INNER_W / 6] * 6,
    )

    bd, wd = s["best_day"], s["worst_day"]
    highlights = _data_table(
        [
            ["", "Day", "Day of Week", "Weather", "Attendance", "Revenue"],
            ["BEST DAY",  str(bd["day"]), bd["day_of_week"], bd["weather"],
             _fmt_int(bd["attendance"]), _fmt_money(bd["revenue"])],
            ["WORST DAY", str(wd["day"]), wd["day_of_week"], wd["weather"],
             _fmt_int(wd["attendance"]), _fmt_money(wd["revenue"])],
        ],
        col_widths=[INNER_W * 0.14, INNER_W * 0.08, INNER_W * 0.18,
                    INNER_W * 0.14, INNER_W * 0.22, INNER_W * 0.24],
    )

    quick = _data_table(
        [
            ["Most Popular Ride", "Top Grossing Store"],
            [s["most_popular_ride"], s["top_grossing_store"]],
        ],
        col_widths=[INNER_W / 2, INNER_W / 2],
    )

    content = _inner([[kpi], [highlights], [quick]])
    _card("Section 1: Executive Summary", content, story)


def _section_daily_trends(story, data):
    daily = data["daily_data"]
    days  = [d["day"] for d in daily]
    pt_c  = [W_COLORS_HEX[d["weather"]] for d in daily]
    patches = [mpatches.Patch(color=c, label=w) for w, c in W_COLORS_HEX.items()]

    def _line_chart(yvals, ylabel, title, line_color):
        fig, ax = plt.subplots(figsize=(CHART_FULL_W, CHART_FULL_H))
        ax.plot(days, yvals, color=line_color, linewidth=1.5, zorder=1)
        ax.scatter(days, yvals, c=pt_c, s=22, zorder=2, edgecolors="none")
        ax.set_xlabel("Day")
        ax.set_ylabel(ylabel)
        ax.set_title(title, fontweight="bold")
        ax.legend(handles=patches, fontsize=7, loc="upper right",
                  framealpha=0.8, facecolor="#f5e6c8", edgecolor="#6b4c11")
        ax.grid(axis="y", alpha=0.5)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        return fig

    attendance = [d["attendance"] for d in daily]
    revenue    = [d["total_revenue"] for d in daily]

    img1 = _fig(
        _line_chart(attendance, "Visitors", "Daily Attendance", "#3d2b00"),
        CHART_FULL_W, CHART_FULL_H,
    )
    img2 = _fig(
        _line_chart(revenue, "Revenue ($)", "Daily Total Revenue", "#2e7ab8"),
        CHART_FULL_W, CHART_FULL_H,
    )
    content = _inner([[img1], [img2]])
    _card("Section 2: Daily Attendance & Revenue Trends", content, story)


def _section_revenue_breakdown(story, data):
    s = data["summary"]
    labels = ["Ticket Revenue", "Food & Beverage", "Retail & Merch"]
    values = [
        s["total_ticket_revenue"],
        s["total_food_beverage_revenue"],
        s["total_retail_merchandise_revenue"],
    ]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(CHART_FULL_W, CHART_HALF_H))
    wedges, texts, autos = ax1.pie(
        values, labels=labels, autopct="%1.1f%%", colors=REV_HEX, startangle=90,
        textprops={"fontsize": 7}, wedgeprops={"linewidth": 1.5, "edgecolor": "#f5e6c8"},
    )
    for a in autos:
        a.set_fontsize(7); a.set_color("white")
    ax1.set_title("Revenue Mix", fontweight="bold")

    dow_totals = {d: {"rev": 0.0, "cnt": 0} for d in DOW_ORDER}
    for d in data["daily_data"]:
        dow_totals[d["day_of_week"]]["rev"] += d["total_revenue"]
        dow_totals[d["day_of_week"]]["cnt"] += 1
    avgs = [dow_totals[d]["rev"] / dow_totals[d]["cnt"] if dow_totals[d]["cnt"] else 0
            for d in DOW_ORDER]
    bar_c = [REV_HEX[2] if d in ("Saturday", "Sunday") else REV_HEX[0] for d in DOW_ORDER]
    ax2.bar([d[:3] for d in DOW_ORDER], avgs, color=bar_c, edgecolor="#f5e6c8", linewidth=1)
    ax2.set_title("Avg Revenue by Day of Week", fontweight="bold")
    ax2.set_ylabel("Avg Revenue ($)")
    ax2.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"${x:,.0f}"))
    ax2.grid(axis="y", alpha=0.5)
    ax2.spines["top"].set_visible(False); ax2.spines["right"].set_visible(False)
    ax2.legend(
        handles=[mpatches.Patch(color=REV_HEX[0], label="Weekday"),
                 mpatches.Patch(color=REV_HEX[2], label="Weekend")],
        fontsize=7, facecolor="#f5e6c8", edgecolor="#6b4c11",
    )
    fig.tight_layout()
    _card("Section 3: Revenue Breakdown",
          _inner([[_fig(fig, CHART_FULL_W, CHART_HALF_H)]]), story)


def _section_ride_analytics(story, data):
    ride_stats = data["ride_stats"]
    names = list(ride_stats.keys())
    riders = [ride_stats[n]["total_riders"] for n in names]
    utils  = [ride_stats[n]["avg_utilization"] * 100 for n in names]
    order  = sorted(range(len(names)), key=lambda i: riders[i], reverse=True)
    sn     = [names[i] for i in order]
    sr     = [riders[i] for i in order]
    su     = [utils[i] for i in order]
    y      = range(len(sn))

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(CHART_FULL_W, CHART_HALF_H))
    ax1.barh(y, sr, color=RIDE_HEX, edgecolor="#f5e6c8", linewidth=1)
    ax1.set_yticks(y); ax1.set_yticklabels(sn, fontsize=7)
    ax1.set_xlabel("Total Riders"); ax1.set_title("Total Riders per Ride", fontweight="bold")
    ax1.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{int(x):,}"))
    ax1.grid(axis="x", alpha=0.5)
    ax1.spines["top"].set_visible(False); ax1.spines["right"].set_visible(False)

    uc = ["#d43030" if u > 80 else RIDE_HEX for u in su]
    ax2.barh(y, su, color=uc, edgecolor="#f5e6c8", linewidth=1)
    ax2.set_yticks(y); ax2.set_yticklabels(sn, fontsize=7)
    ax2.set_xlabel("Utilization (%)"); ax2.set_title("Avg Queue Utilization", fontweight="bold")
    ax2.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x:.0f}%"))
    ax2.grid(axis="x", alpha=0.5)
    ax2.spines["top"].set_visible(False); ax2.spines["right"].set_visible(False)
    fig.tight_layout()
    chart_img = _fig(fig, CHART_FULL_W, CHART_HALF_H)

    incidents = data["incidents"]
    if incidents:
        cw = [INNER_W * 0.12, INNER_W * 0.65, INNER_W * 0.23]
        inc_rows = [["Day", "Ride", "Hours Down"]]
        inc_rows += [[str(i["day"]), i["ride"], str(i["hours_down"])] for i in incidents]
        inc_table = _data_table(inc_rows, col_widths=cw)
        content = _inner([[chart_img], [inc_table]])
    else:
        content = _inner([[chart_img],
                          [Paragraph("No breakdown incidents recorded.", SMALL_STYLE)]])

    _card("Section 4: Ride Analytics", content, story)


def _section_store_analytics(story, data):
    store_stats = data["store_stats"]
    stores = list(store_stats.keys())
    revs   = [store_stats[s]["total_revenue"] for s in stores]
    cats   = [store_stats[s]["category"] for s in stores]
    order  = sorted(range(len(stores)), key=lambda i: revs[i], reverse=True)
    ss     = [stores[i] for i in order]
    sr     = [revs[i] for i in order]
    sc     = [cats[i] for i in order]
    bar_c  = [FB_HEX if c == "food_beverage" else RETAIL_HEX for c in sc]
    y      = range(len(ss))

    fig, ax = plt.subplots(figsize=(CHART_FULL_W, 4.2))
    ax.barh(y, sr, color=bar_c, edgecolor="#f5e6c8", linewidth=1)
    ax.set_yticks(y); ax.set_yticklabels(ss, fontsize=7)
    ax.set_xlabel("Total Revenue ($)")
    ax.set_title("Total Revenue by Store / Restaurant", fontweight="bold")
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"${x:,.0f}"))
    ax.grid(axis="x", alpha=0.5)
    ax.spines["top"].set_visible(False); ax.spines["right"].set_visible(False)
    ax.legend(handles=[mpatches.Patch(color=FB_HEX, label="Food & Bev"),
                       mpatches.Patch(color=RETAIL_HEX, label="Retail")],
              fontsize=7, facecolor="#f5e6c8", edgecolor="#6b4c11", loc="lower right")
    fig.tight_layout()
    store_img = _fig(fig, CHART_FULL_W, 3.8)

    daily = data["daily_data"]
    use_dow = len(daily) > 60
    if use_dow:
        agg = {d: {"fb": 0.0, "ret": 0.0, "cnt": 0} for d in DOW_ORDER}
        for d in daily:
            agg[d["day_of_week"]]["fb"]  += d["food_beverage_revenue"]
            agg[d["day_of_week"]]["ret"] += d["retail_merchandise_revenue"]
            agg[d["day_of_week"]]["cnt"] += 1
        labels  = [d[:3] for d in DOW_ORDER]
        avg_fb  = [agg[d]["fb"] / agg[d]["cnt"] if agg[d]["cnt"] else 0 for d in DOW_ORDER]
        avg_ret = [agg[d]["ret"] / agg[d]["cnt"] if agg[d]["cnt"] else 0 for d in DOW_ORDER]
        title2  = "Avg F&B vs Retail by Day of Week"
    else:
        labels  = [str(d["day"]) for d in daily]
        avg_fb  = [d["food_beverage_revenue"] for d in daily]
        avg_ret = [d["retail_merchandise_revenue"] for d in daily]
        title2  = "Food & Bev vs Retail Revenue per Day"

    fig2, ax2 = plt.subplots(figsize=(CHART_FULL_W, CHART_FULL_H))
    w = 0.38; x = range(len(labels))
    ax2.bar([i - w/2 for i in x], avg_fb, width=w, label="Food & Bev",
            color=FB_HEX, edgecolor="#f5e6c8", linewidth=0.5)
    ax2.bar([i + w/2 for i in x], avg_ret, width=w, label="Retail",
            color=RETAIL_HEX, edgecolor="#f5e6c8", linewidth=0.5)
    ax2.set_xticks(list(x))
    ax2.set_xticklabels(labels, fontsize=6 if not use_dow else 8,
                        rotation=45 if not use_dow else 0)
    ax2.set_ylabel("Revenue ($)"); ax2.set_title(title2, fontweight="bold")
    ax2.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"${v:,.0f}"))
    ax2.legend(fontsize=7, facecolor="#f5e6c8", edgecolor="#6b4c11")
    ax2.grid(axis="y", alpha=0.5)
    ax2.spines["top"].set_visible(False); ax2.spines["right"].set_visible(False)
    fig2.tight_layout()
    daily_img = _fig(fig2, CHART_FULL_W, CHART_FULL_H)

    _card("Section 5: Store & Restaurant Analytics",
          _inner([[store_img], [daily_img]]), story)


def _section_demographics(story, data):
    arch = data["summary"]["archetype_totals"]
    names  = [k for k, v in arch.items() if v > 0]
    values = [arch[k] for k in names]
    daily  = data["daily_data"]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(CHART_FULL_W, CHART_HALF_H))
    wedges, texts, autos = ax1.pie(
        values, labels=names, autopct="%1.0f%%",
        colors=ARCH_HEX[:len(names)], startangle=90,
        textprops={"fontsize": 6},
        wedgeprops={"linewidth": 1.5, "edgecolor": "#f5e6c8"},
    )
    for a in autos: a.set_fontsize(6); a.set_color("white")
    ax1.set_title("Archetype Distribution", fontweight="bold")

    days  = [d["day"] for d in daily]
    spend = [d["avg_spend_per_visitor"] for d in daily]
    ax2.plot(days, spend, color="#6b4c11", linewidth=1.8)
    ax2.fill_between(days, spend, alpha=0.15, color="#6b4c11")
    ax2.set_xlabel("Day"); ax2.set_ylabel("Avg Spend ($)")
    ax2.set_title("Avg Spend per Visitor per Day", fontweight="bold")
    ax2.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"${x:,.0f}"))
    ax2.grid(alpha=0.5)
    ax2.spines["top"].set_visible(False); ax2.spines["right"].set_visible(False)
    fig.tight_layout()
    chart_img = _fig(fig, CHART_FULL_W, CHART_HALF_H)

    ts = data["ticket_stats"]
    total_cnt = sum(v["count"] for v in ts.values())
    total_rev = sum(v["revenue"] for v in ts.values())
    ticket_rows = [["Ticket Type", "Count", "Revenue"]]
    for t, s in ts.items():
        ticket_rows.append([t.capitalize(), _fmt_int(s["count"]), _fmt_money(s["revenue"])])
    ticket_rows.append(["TOTAL", _fmt_int(total_cnt), _fmt_money(total_rev)])
    cw = [INNER_W * 0.35, INNER_W * 0.30, INNER_W * 0.35]
    ticket_table = _data_table(ticket_rows, col_widths=cw)

    _card("Section 6: Visitor Demographics",
          _inner([[chart_img], [ticket_table]]), story)


def _section_weather(story, data):
    ws = data["summary"]["weather_summary"]
    rows = [["Weather", "Days", "Avg Attendance", "Avg Revenue"]]
    for state in ("Sunny", "Cloudy", "Rainy"):
        s = ws.get(state, {"count": 0, "avg_attendance": 0, "avg_revenue": 0.0})
        rows.append([state, str(s["count"]),
                     _fmt_int(int(s["avg_attendance"])), _fmt_money(s["avg_revenue"])])
    t = _data_table(rows, col_widths=[INNER_W * 0.25] * 4)
    _card("Section 7: Weather Impact", _inner([[t]]), story)


def _section_incidents(story, data):
    incidents = data["incidents"]
    if not incidents:
        content = _inner([[Paragraph("No incidents were recorded.", SMALL_STYLE)]])
    else:
        rows = [["Day", "Ride", "Hours Affected"]]
        rows += [[str(i["day"]), i["ride"], str(i["hours_down"])] for i in incidents]
        cw = [INNER_W * 0.12, INNER_W * 0.65, INNER_W * 0.23]
        content = _inner([[_data_table(rows, col_widths=cw)]])
    _card("Section 8: Incidents Log", content, story)


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def generate_pdf_report(data: dict) -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=letter,
        leftMargin=MARGIN, rightMargin=MARGIN,
        topMargin=MARGIN, bottomMargin=MARGIN,
    )

    days = data["summary"]["total_days"]

    title_card = Table(
        [[Paragraph("AMUSEMENT PARK SIMULATION REPORT", H1_STYLE)],
         [Paragraph(f"{days}-Day Simulation", SUB_STYLE)]],
        colWidths=[CONTENT_W],
    )
    title_card.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), BROWN_DARK),
        ("BOX",           (0, 0), (-1, -1), 3, BROWN),
        ("TOPPADDING",    (0, 0), (-1, -1), 14),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 14),
        ("LEFTPADDING",   (0, 0), (-1, -1), 12),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 12),
    ]))

    story = [title_card, Spacer(1, 18)]

    _section_summary(story, data)
    story.append(PageBreak())
    _section_daily_trends(story, data)
    story.append(PageBreak())
    _section_revenue_breakdown(story, data)
    story.append(PageBreak())
    _section_ride_analytics(story, data)
    story.append(PageBreak())
    _section_store_analytics(story, data)
    story.append(PageBreak())
    _section_demographics(story, data)
    story.append(PageBreak())
    _section_weather(story, data)
    story.append(Spacer(1, 14))
    _section_incidents(story, data)

    doc.build(story, onFirstPage=_page_bg, onLaterPages=_page_bg)
    buf.seek(0)
    return buf.read()
