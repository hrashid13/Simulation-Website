import io
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.ticker as mticker

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    Image as RLImage, PageBreak, HRFlowable,
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT

PAGE_W, PAGE_H = letter
MARGIN = 0.75 * inch
CONTENT_W = PAGE_W - 2 * MARGIN

BLUE_DARK = "#1A237E"
BLUE_MID = "#1565C0"
BLUE_LIGHT = "#E8EAF6"
BORDER_COLOR = "#9FA8DA"

W_COLORS = {"Sunny": "#F9A825", "Cloudy": "#90A4AE", "Rainy": "#42A5F5"}
REV_COLORS = ["#1565C0", "#2E7D32", "#E65100"]
ARCH_COLORS = ["#EF5350", "#42A5F5", "#66BB6A", "#FFA726", "#AB47BC", "#26C6DA"]


def _styles():
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle("DocTitle", parent=base["Title"],
                                fontSize=26, textColor=colors.HexColor(BLUE_DARK),
                                alignment=TA_CENTER, spaceAfter=6),
        "subtitle": ParagraphStyle("DocSub", parent=base["Normal"],
                                   fontSize=11, textColor=colors.HexColor("#546E7A"),
                                   alignment=TA_CENTER, spaceAfter=24),
        "h2": ParagraphStyle("H2", parent=base["Heading2"],
                             fontSize=13, textColor=colors.HexColor(BLUE_MID),
                             spaceBefore=10, spaceAfter=6),
        "body": ParagraphStyle("Body", parent=base["Normal"], fontSize=9, spaceAfter=3),
        "small": ParagraphStyle("Small", parent=base["Normal"], fontSize=8,
                                textColor=colors.HexColor("#546E7A")),
    }


def _table(rows, col_widths=None):
    n = len(rows)
    bg_list = [colors.white, colors.HexColor(BLUE_LIGHT)]
    commands = [
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(BLUE_MID)),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor(BORDER_COLOR)),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]
    for i in range(1, n):
        if i % 2 == 0:
            commands.append(("BACKGROUND", (0, i), (-1, i), colors.HexColor(BLUE_LIGHT)))
    t = Table(rows, colWidths=col_widths)
    t.setStyle(TableStyle(commands))
    return t


def _hr():
    return HRFlowable(width="100%", thickness=0.5,
                      color=colors.HexColor(BORDER_COLOR), spaceAfter=8)


def _fig_to_image(fig, w=6.5, h=3.2):
    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight", dpi=140)
    plt.close(fig)
    buf.seek(0)
    return RLImage(buf, width=w * inch, height=h * inch)


def _fmt_money(v):
    return f"${v:,.2f}"


def _fmt_int(v):
    return f"{v:,}"


# ---------------------------------------------------------------------------
# Section builders
# ---------------------------------------------------------------------------

def _section_executive_summary(story, st, data):
    s = data["summary"]
    story.append(Paragraph("Section 1: Executive Summary", st["h2"]))
    story.append(_hr())

    kpi_rows = [
        ["Simulation Period", "Total Attendance", "Total Revenue"],
        [
            f"{s['total_days']} days",
            _fmt_int(s["total_attendance"]),
            _fmt_money(s["total_revenue"]),
        ],
        ["Ticket Revenue", "Food & Bev Revenue", "Retail Revenue"],
        [
            _fmt_money(s["total_ticket_revenue"]),
            _fmt_money(s["total_food_beverage_revenue"]),
            _fmt_money(s["total_retail_merchandise_revenue"]),
        ],
    ]
    story.append(_table(kpi_rows, col_widths=[CONTENT_W / 3] * 3))
    story.append(Spacer(1, 10))

    bd = s["best_day"]
    wd = s["worst_day"]
    highlight_rows = [
        ["Metric", "Day", "Day of Week", "Weather", "Attendance", "Revenue"],
        ["Best Day", str(bd["day"]), bd["day_of_week"], bd["weather"],
         _fmt_int(bd["attendance"]), _fmt_money(bd["revenue"])],
        ["Worst Day", str(wd["day"]), wd["day_of_week"], wd["weather"],
         _fmt_int(wd["attendance"]), _fmt_money(wd["revenue"])],
    ]
    cw = CONTENT_W / 6
    story.append(_table(highlight_rows, col_widths=[cw] * 6))
    story.append(Spacer(1, 10))

    quick_rows = [
        ["Most Popular Ride", "Top Grossing Store"],
        [s["most_popular_ride"], s["top_grossing_store"]],
    ]
    story.append(_table(quick_rows, col_widths=[CONTENT_W / 2] * 2))


def _section_daily_trends(story, st, data):
    story.append(Paragraph("Section 2: Daily Attendance & Revenue Trends", st["h2"]))
    story.append(_hr())

    daily = data["daily_data"]
    days = [d["day"] for d in daily]
    attendance = [d["attendance"] for d in daily]
    revenue = [d["total_revenue"] for d in daily]
    pt_colors = [W_COLORS[d["weather"]] for d in daily]

    legend_patches = [mpatches.Patch(color=c, label=w) for w, c in W_COLORS.items()]

    fig, ax = plt.subplots(figsize=(9, 2.8))
    ax.plot(days, attendance, color="#37474F", linewidth=1.2, zorder=1)
    ax.scatter(days, attendance, c=pt_colors, s=20, zorder=2, edgecolors="none")
    ax.set_xlabel("Day", fontsize=8)
    ax.set_ylabel("Visitors", fontsize=8)
    ax.set_title("Daily Attendance", fontsize=10, fontweight="bold")
    ax.tick_params(labelsize=7)
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{int(x):,}"))
    ax.grid(axis="y", alpha=0.3, linewidth=0.5)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.legend(handles=legend_patches, fontsize=7, loc="upper right", framealpha=0.7)
    fig.tight_layout()
    story.append(_fig_to_image(fig, 6.5, 2.8))
    story.append(Spacer(1, 8))

    fig, ax = plt.subplots(figsize=(9, 2.8))
    ax.plot(days, revenue, color="#1B5E20", linewidth=1.2, zorder=1)
    ax.scatter(days, revenue, c=pt_colors, s=20, zorder=2, edgecolors="none")
    ax.set_xlabel("Day", fontsize=8)
    ax.set_ylabel("Revenue ($)", fontsize=8)
    ax.set_title("Daily Total Revenue", fontsize=10, fontweight="bold")
    ax.tick_params(labelsize=7)
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"${x:,.0f}"))
    ax.grid(axis="y", alpha=0.3, linewidth=0.5)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.legend(handles=legend_patches, fontsize=7, loc="upper right", framealpha=0.7)
    fig.tight_layout()
    story.append(_fig_to_image(fig, 6.5, 2.8))


def _section_revenue_breakdown(story, st, data):
    story.append(Paragraph("Section 3: Revenue Breakdown", st["h2"]))
    story.append(_hr())

    s = data["summary"]
    rev_labels = ["Ticket Revenue", "Food & Beverage", "Retail & Merchandise"]
    rev_values = [
        s["total_ticket_revenue"],
        s["total_food_beverage_revenue"],
        s["total_retail_merchandise_revenue"],
    ]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(9, 3.2))

    wedges, texts, autotexts = ax1.pie(
        rev_values, labels=rev_labels, autopct="%1.1f%%",
        colors=REV_COLORS, startangle=90,
        textprops={"fontsize": 7},
        wedgeprops={"linewidth": 0.5, "edgecolor": "white"},
    )
    for at in autotexts:
        at.set_fontsize(7)
        at.set_color("white")
    ax1.set_title("Revenue Mix", fontsize=10, fontweight="bold")

    dow_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    dow_totals = {d: {"revenue": 0.0, "count": 0} for d in dow_order}
    for d in data["daily_data"]:
        dow = d["day_of_week"]
        dow_totals[dow]["revenue"] += d["total_revenue"]
        dow_totals[dow]["count"] += 1

    dow_labels = [d[:3] for d in dow_order]
    dow_avgs = [
        dow_totals[d]["revenue"] / dow_totals[d]["count"] if dow_totals[d]["count"] else 0
        for d in dow_order
    ]
    bar_colors = [REV_COLORS[2] if d in ("Saturday", "Sunday") else REV_COLORS[0] for d in dow_order]
    bars = ax2.bar(dow_labels, dow_avgs, color=bar_colors, edgecolor="white", linewidth=0.5)
    ax2.set_title("Avg Revenue by Day of Week", fontsize=10, fontweight="bold")
    ax2.set_ylabel("Avg Revenue ($)", fontsize=8)
    ax2.tick_params(labelsize=7)
    ax2.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"${x:,.0f}"))
    ax2.grid(axis="y", alpha=0.3, linewidth=0.5)
    ax2.spines["top"].set_visible(False)
    ax2.spines["right"].set_visible(False)
    weekend_patch = mpatches.Patch(color=REV_COLORS[2], label="Weekend")
    weekday_patch = mpatches.Patch(color=REV_COLORS[0], label="Weekday")
    ax2.legend(handles=[weekday_patch, weekend_patch], fontsize=7)

    fig.tight_layout()
    story.append(_fig_to_image(fig, 6.5, 3.2))


def _section_ride_analytics(story, st, data):
    story.append(Paragraph("Section 4: Ride Analytics", st["h2"]))
    story.append(_hr())

    ride_stats = data["ride_stats"]
    ride_names = list(ride_stats.keys())
    total_riders = [ride_stats[r]["total_riders"] for r in ride_names]
    utilization = [ride_stats[r]["avg_utilization"] * 100 for r in ride_names]

    order = sorted(range(len(ride_names)), key=lambda i: total_riders[i], reverse=True)
    sorted_names = [ride_names[i] for i in order]
    sorted_riders = [total_riders[i] for i in order]
    sorted_util = [utilization[i] for i in order]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(9, 3.5))

    y = range(len(sorted_names))
    ax1.barh(y, sorted_riders, color="#5C6BC0", edgecolor="white", linewidth=0.5)
    ax1.set_yticks(y)
    ax1.set_yticklabels(sorted_names, fontsize=7)
    ax1.set_xlabel("Total Riders", fontsize=8)
    ax1.set_title("Total Riders per Ride", fontsize=10, fontweight="bold")
    ax1.tick_params(labelsize=7)
    ax1.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{int(x):,}"))
    ax1.grid(axis="x", alpha=0.3, linewidth=0.5)
    ax1.spines["top"].set_visible(False)
    ax1.spines["right"].set_visible(False)

    util_colors = ["#EF5350" if u > 80 else "#5C6BC0" for u in sorted_util]
    ax2.barh(y, sorted_util, color=util_colors, edgecolor="white", linewidth=0.5)
    ax2.set_yticks(y)
    ax2.set_yticklabels(sorted_names, fontsize=7)
    ax2.set_xlabel("Capacity Utilization (%)", fontsize=8)
    ax2.set_title("Avg Queue Utilization", fontsize=10, fontweight="bold")
    ax2.tick_params(labelsize=7)
    ax2.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x:.1f}%"))
    ax2.grid(axis="x", alpha=0.3, linewidth=0.5)
    ax2.spines["top"].set_visible(False)
    ax2.spines["right"].set_visible(False)

    fig.tight_layout()
    story.append(_fig_to_image(fig, 6.5, 3.2))
    story.append(Spacer(1, 8))

    incidents = data["incidents"]
    if incidents:
        inc_rows = [["Day", "Ride", "Hours Down"]]
        for inc in incidents:
            inc_rows.append([str(inc["day"]), inc["ride"], str(inc["hours_down"])])
        cw = [CONTENT_W * 0.15, CONTENT_W * 0.65, CONTENT_W * 0.20]
        story.append(Paragraph("Ride Breakdown Incidents", st["body"]))
        story.append(_table(inc_rows, col_widths=cw))
    else:
        story.append(Paragraph("No ride breakdown incidents recorded.", st["small"]))


def _section_store_analytics(story, st, data):
    story.append(Paragraph("Section 5: Store & Restaurant Analytics", st["h2"]))
    story.append(_hr())

    store_stats = data["store_stats"]
    stores = list(store_stats.keys())
    revenues = [store_stats[s]["total_revenue"] for s in stores]
    categories = [store_stats[s]["category"] for s in stores]

    order = sorted(range(len(stores)), key=lambda i: revenues[i], reverse=True)
    sorted_stores = [stores[i] for i in order]
    sorted_revenues = [revenues[i] for i in order]
    sorted_cats = [categories[i] for i in order]
    bar_colors = ["#2E7D32" if c == "food_beverage" else "#E65100" for c in sorted_cats]

    fig, ax = plt.subplots(figsize=(9, 4.5))
    y = range(len(sorted_stores))
    ax.barh(y, sorted_revenues, color=bar_colors, edgecolor="white", linewidth=0.5)
    ax.set_yticks(y)
    ax.set_yticklabels(sorted_stores, fontsize=7)
    ax.set_xlabel("Total Revenue ($)", fontsize=8)
    ax.set_title("Total Revenue by Store / Restaurant", fontsize=10, fontweight="bold")
    ax.tick_params(labelsize=7)
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"${x:,.0f}"))
    ax.grid(axis="x", alpha=0.3, linewidth=0.5)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fb_patch = mpatches.Patch(color="#2E7D32", label="Food & Beverage")
    ret_patch = mpatches.Patch(color="#E65100", label="Retail & Merchandise")
    ax.legend(handles=[fb_patch, ret_patch], fontsize=7, loc="lower right")
    fig.tight_layout()
    story.append(_fig_to_image(fig, 6.5, 4.0))
    story.append(Spacer(1, 8))

    daily = data["daily_data"]
    if len(daily) <= 60:
        fb_daily = [d["food_beverage_revenue"] for d in daily]
        ret_daily = [d["retail_merchandise_revenue"] for d in daily]
        days = [d["day"] for d in daily]

        fig, ax = plt.subplots(figsize=(9, 2.8))
        width = 0.4
        x = range(len(days))
        ax.bar([i - width / 2 for i in x], fb_daily, width=width, label="Food & Bev",
               color="#2E7D32", edgecolor="white", linewidth=0.3)
        ax.bar([i + width / 2 for i in x], ret_daily, width=width, label="Retail",
               color="#E65100", edgecolor="white", linewidth=0.3)
        ax.set_xticks(list(x))
        ax.set_xticklabels(days, fontsize=6, rotation=45)
        ax.set_ylabel("Revenue ($)", fontsize=8)
        ax.set_title("Food & Bev vs Retail Revenue per Day", fontsize=10, fontweight="bold")
        ax.tick_params(labelsize=7)
        ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"${v:,.0f}"))
        ax.legend(fontsize=7)
        ax.grid(axis="y", alpha=0.3, linewidth=0.5)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        fig.tight_layout()
        story.append(_fig_to_image(fig, 6.5, 2.8))
    else:
        dow_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        dow_fb = {d: 0.0 for d in dow_order}
        dow_ret = {d: 0.0 for d in dow_order}
        dow_cnt = {d: 0 for d in dow_order}
        for d in daily:
            dow = d["day_of_week"]
            dow_fb[dow] += d["food_beverage_revenue"]
            dow_ret[dow] += d["retail_merchandise_revenue"]
            dow_cnt[dow] += 1

        labels = [d[:3] for d in dow_order]
        avg_fb = [dow_fb[d] / dow_cnt[d] if dow_cnt[d] else 0 for d in dow_order]
        avg_ret = [dow_ret[d] / dow_cnt[d] if dow_cnt[d] else 0 for d in dow_order]

        fig, ax = plt.subplots(figsize=(9, 2.8))
        width = 0.35
        x = range(len(labels))
        ax.bar([i - width / 2 for i in x], avg_fb, width=width, label="Food & Bev",
               color="#2E7D32", edgecolor="white")
        ax.bar([i + width / 2 for i in x], avg_ret, width=width, label="Retail",
               color="#E65100", edgecolor="white")
        ax.set_xticks(list(x))
        ax.set_xticklabels(labels, fontsize=8)
        ax.set_ylabel("Avg Revenue ($)", fontsize=8)
        ax.set_title("Avg Food & Bev vs Retail by Day of Week", fontsize=10, fontweight="bold")
        ax.tick_params(labelsize=7)
        ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"${v:,.0f}"))
        ax.legend(fontsize=7)
        ax.grid(axis="y", alpha=0.3, linewidth=0.5)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        fig.tight_layout()
        story.append(_fig_to_image(fig, 6.5, 2.8))


def _section_visitor_demographics(story, st, data):
    story.append(Paragraph("Section 6: Visitor Demographics", st["h2"]))
    story.append(_hr())

    arch_totals = data["summary"]["archetype_totals"]
    arch_names = [k for k, v in arch_totals.items() if v > 0]
    arch_values = [arch_totals[k] for k in arch_names]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(9, 3.2))

    wedges, texts, autotexts = ax1.pie(
        arch_values, labels=arch_names, autopct="%1.1f%%",
        colors=ARCH_COLORS[:len(arch_names)], startangle=90,
        textprops={"fontsize": 6},
        wedgeprops={"linewidth": 0.5, "edgecolor": "white"},
    )
    for at in autotexts:
        at.set_fontsize(6)
        at.set_color("white")
    ax1.set_title("Visitor Archetype Distribution", fontsize=10, fontweight="bold")

    daily = data["daily_data"]
    days = [d["day"] for d in daily]
    avg_spend = [d["avg_spend_per_visitor"] for d in daily]
    ax2.plot(days, avg_spend, color="#7B1FA2", linewidth=1.2)
    ax2.set_xlabel("Day", fontsize=8)
    ax2.set_ylabel("Avg Spend ($)", fontsize=8)
    ax2.set_title("Avg Spend per Visitor per Day", fontsize=10, fontweight="bold")
    ax2.tick_params(labelsize=7)
    ax2.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"${x:,.0f}"))
    ax2.grid(alpha=0.3, linewidth=0.5)
    ax2.spines["top"].set_visible(False)
    ax2.spines["right"].set_visible(False)

    fig.tight_layout()
    story.append(_fig_to_image(fig, 6.5, 3.2))
    story.append(Spacer(1, 8))

    ticket_stats = data["ticket_stats"]
    ticket_rows = [["Ticket Type", "Count", "Revenue"]]
    total_tickets = sum(v["count"] for v in ticket_stats.values())
    total_ticket_rev = sum(v["revenue"] for v in ticket_stats.values())
    for t_type, stats in ticket_stats.items():
        ticket_rows.append([
            t_type.capitalize(),
            _fmt_int(stats["count"]),
            _fmt_money(stats["revenue"]),
        ])
    ticket_rows.append(["Total", _fmt_int(total_tickets), _fmt_money(total_ticket_rev)])
    cw = [CONTENT_W * 0.35, CONTENT_W * 0.30, CONTENT_W * 0.35]
    story.append(_table(ticket_rows, col_widths=cw))


def _section_weather_impact(story, st, data):
    story.append(Paragraph("Section 7: Weather Impact", st["h2"]))
    story.append(_hr())

    ws = data["summary"]["weather_summary"]
    rows = [["Weather", "Days", "Avg Attendance", "Avg Revenue"]]
    for state in ("Sunny", "Cloudy", "Rainy"):
        stats = ws.get(state, {"count": 0, "avg_attendance": 0, "avg_revenue": 0.0})
        rows.append([
            state,
            str(stats["count"]),
            _fmt_int(int(stats["avg_attendance"])),
            _fmt_money(stats["avg_revenue"]),
        ])
    cw = [CONTENT_W * 0.25] * 4
    story.append(_table(rows, col_widths=cw))


def _section_incidents_log(story, st, data):
    story.append(Paragraph("Section 8: Incidents Log", st["h2"]))
    story.append(_hr())

    incidents = data["incidents"]
    if not incidents:
        story.append(Paragraph("No incidents were recorded during this simulation.", st["small"]))
        return

    rows = [["Day", "Ride", "Hours Affected"]]
    for inc in incidents:
        rows.append([str(inc["day"]), inc["ride"], str(inc["hours_down"])])
    cw = [CONTENT_W * 0.15, CONTENT_W * 0.65, CONTENT_W * 0.20]
    story.append(_table(rows, col_widths=cw))


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def generate_pdf_report(data: dict) -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=letter,
        leftMargin=MARGIN,
        rightMargin=MARGIN,
        topMargin=MARGIN,
        bottomMargin=MARGIN,
    )

    st = _styles()
    story = []

    days = data["summary"]["total_days"]
    story.append(Paragraph("Amusement Park Simulation Report", st["title"]))
    story.append(Paragraph(f"{days}-Day Simulation", st["subtitle"]))
    story.append(Spacer(1, 10))

    _section_executive_summary(story, st, data)
    story.append(PageBreak())

    _section_daily_trends(story, st, data)
    story.append(PageBreak())

    _section_revenue_breakdown(story, st, data)
    story.append(PageBreak())

    _section_ride_analytics(story, st, data)
    story.append(PageBreak())

    _section_store_analytics(story, st, data)
    story.append(PageBreak())

    _section_visitor_demographics(story, st, data)
    story.append(PageBreak())

    _section_weather_impact(story, st, data)
    story.append(Spacer(1, 20))
    _section_incidents_log(story, st, data)

    doc.build(story)
    buf.seek(0)
    return buf.read()
