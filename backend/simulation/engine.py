import random

from .weather import roll_weather
from .attendance import calculate_attendance, get_day_of_week, is_weekend
from .archetypes import (
    ARCHETYPES,
    WEEKDAY_ARCHETYPES,
    get_weekday_weights,
    get_weekend_weights,
    TICKET_PRICES,
)
from .rides import RIDES
from .stores import FOOD_AND_BEVERAGE, RETAIL_AND_MERCHANDISE, ALL_STORES

PARK_OPEN_HOURS = 10


def _resolve_ticket_mix(ticket_mix: dict, group_size: int) -> dict:
    tickets = {"adult": 0, "child": 0, "toddler": 0, "senior": 0}

    all_key = next((k for k, v in ticket_mix.items() if v == "all"), None)
    rest_key = next((k for k, v in ticket_mix.items() if v == "rest"), None)

    if all_key:
        tickets[all_key] = group_size
    elif rest_key:
        for k, v in ticket_mix.items():
            if v != "rest":
                tickets[k] = min(v, group_size)
        tickets[rest_key] = max(0, group_size - sum(tickets.values()))
    else:
        total_in_mix = sum(ticket_mix.values())
        for k, v in ticket_mix.items():
            tickets[k] = round(group_size * v / total_in_mix)
        diff = group_size - sum(tickets.values())
        if diff != 0:
            dominant = max(ticket_mix, key=ticket_mix.get)
            tickets[dominant] = max(0, tickets[dominant] + diff)

    return tickets


def _simulate_day(
    day_number: int,
    run_ride_mods: dict,
    run_store_mods: dict,
    run_food_scale: float,
    run_retail_scale: float,
) -> dict:
    weather = roll_weather()
    attendance, day_of_week = calculate_attendance(day_number, weather["attendance_multiplier"])
    weekday = not is_weekend(day_of_week)

    # Per-day modifiers: each day has its own independent popularity shifts
    day_ride_mods = {r["name"]: random.uniform(0.75, 1.35) for r in RIDES}
    day_store_mods = {s["name"]: random.uniform(0.70, 1.40) for s in ALL_STORES}

    ride_status = {}
    incidents = []
    for ride in RIDES:
        closed_by_weather = ride["weather_dependency"] == "closes_on_rain" and weather["aqua_rush_closed"]
        breakdown_hours = 0
        if not closed_by_weather and random.random() < ride["breakdown_probability"]:
            breakdown_hours = random.randint(1, 4)
            incidents.append({
                "day": day_number,
                "ride": ride["name"],
                "hours_down": breakdown_hours,
            })
        operating_hours = 0 if closed_by_weather else max(0, PARK_OPEN_HOURS - breakdown_hours)
        ride_status[ride["name"]] = {
            "available": operating_hours > 0,
            "operating_hours": operating_hours,
            "max_daily_capacity": ride["max_hourly_capacity"] * operating_hours,
        }

    available_rides = [r for r in RIDES if ride_status[r["name"]]["available"]]
    aqua_rush_demand_mult = weather["aqua_rush_demand_multiplier"]

    if weekday:
        archetype_pool = ARCHETYPES
        archetype_weights = get_weekday_weights()
    else:
        archetype_pool = WEEKDAY_ARCHETYPES
        archetype_weights = get_weekend_weights()

    groups = []
    total_generated = 0
    while total_generated < attendance:
        archetype = random.choices(archetype_pool, weights=archetype_weights, k=1)[0]
        min_sz, max_sz = archetype["group_size_range"]
        size = random.randint(min_sz, max_sz)
        remaining = attendance - total_generated
        if size > remaining * 1.1:
            size = max(1, remaining)
        groups.append({"archetype": archetype, "size": size})
        total_generated += size

    ticket_counts = {"adult": 0, "child": 0, "toddler": 0, "senior": 0}
    ticket_revenue = 0.0
    food_revenue = 0.0
    retail_revenue = 0.0
    ride_riders = {r["name"]: 0 for r in RIDES}
    store_revenue = {s["name"]: 0.0 for s in ALL_STORES}
    store_transactions = {s["name"]: 0 for s in ALL_STORES}
    archetype_visitor_counts = {a["name"]: 0 for a in ARCHETYPES}

    # Precompute store weights for the day (run_mod × day_mod × inherent throughput)
    food_weights = [
        s["max_hourly_customers"] * run_store_mods[s["name"]] * day_store_mods[s["name"]]
        for s in FOOD_AND_BEVERAGE
    ]
    merch_weights = [
        s["max_hourly_customers"] * run_store_mods[s["name"]] * day_store_mods[s["name"]]
        for s in RETAIL_AND_MERCHANDISE
    ]

    for group in groups:
        archetype = group["archetype"]
        size = group["size"]
        archetype_visitor_counts[archetype["name"]] += size

        tickets = _resolve_ticket_mix(archetype["ticket_mix"], size)
        for t_type, count in tickets.items():
            ticket_counts[t_type] += count
            ticket_revenue += count * TICKET_PRICES[t_type]

        min_h, max_h = archetype["hours_in_park_range"]
        hours = random.randint(min_h, max_h)

        ride_pool = []
        ride_weights = []
        for ride in available_rides:
            if ride["name"] in archetype["ride_aversions"]:
                continue
            ride_pool.append(ride["name"])
            base_w = 3.0 if ride["name"] in archetype["ride_preferences"] else 1.0
            # Apply per-run and per-day modifiers for ride popularity variance
            base_w *= run_ride_mods[ride["name"]] * day_ride_mods[ride["name"]]
            if ride["name"] == "Aqua Rush":
                base_w *= aqua_rush_demand_mult
            ride_weights.append(base_w)

        if ride_pool:
            rides_attempted = int(hours / 1.5) * size
            if rides_attempted > 0:
                chosen_rides = random.choices(ride_pool, weights=ride_weights, k=rides_attempted)
                for chosen in chosen_rides:
                    ride_riders[chosen] += 1

        # Per-group spending noise (70–130% of expected)
        group_spend_noise = random.uniform(0.70, 1.30)

        food_visits = int(
            size * (hours / 8.0) * 2.0
            * archetype["food_spend_multiplier"]
            * weather["food_spend_multiplier"]
            * run_food_scale
            * group_spend_noise
        )
        if food_visits > 0:
            chosen_fb = random.choices(FOOD_AND_BEVERAGE, weights=food_weights, k=food_visits)
            for store in chosen_fb:
                value = max(0.5, random.gauss(store["avg_transaction_value"], store["avg_transaction_value"] * 0.25))
                store_revenue[store["name"]] += value
                store_transactions[store["name"]] += 1
                food_revenue += value

        merch_visits = int(
            size * (hours / 8.0) * 1.0
            * archetype["merch_spend_multiplier"]
            * run_retail_scale
            * group_spend_noise
        )
        if merch_visits > 0:
            chosen_merch = random.choices(RETAIL_AND_MERCHANDISE, weights=merch_weights, k=merch_visits)
            for store in chosen_merch:
                value = max(0.5, random.gauss(store["avg_transaction_value"], store["avg_transaction_value"] * 0.25))
                store_revenue[store["name"]] += value
                store_transactions[store["name"]] += 1
                retail_revenue += value

    for ride in RIDES:
        cap = ride_status[ride["name"]]["max_daily_capacity"]
        if ride_riders[ride["name"]] > cap:
            ride_riders[ride["name"]] = cap

    total_revenue = ticket_revenue + food_revenue + retail_revenue

    return {
        "day": day_number,
        "day_of_week": day_of_week,
        "weather": weather["state"],
        "attendance": total_generated,
        "ticket_revenue": round(ticket_revenue, 2),
        "food_beverage_revenue": round(food_revenue, 2),
        "retail_merchandise_revenue": round(retail_revenue, 2),
        "total_revenue": round(total_revenue, 2),
        "avg_spend_per_visitor": round(total_revenue / max(1, total_generated), 2),
        "archetype_counts": archetype_visitor_counts,
        "ticket_counts": ticket_counts,
        "ride_riders": ride_riders,
        "ride_operating_hours": {r["name"]: ride_status[r["name"]]["operating_hours"] for r in RIDES},
        "store_revenue": {k: round(v, 2) for k, v in store_revenue.items()},
        "store_transactions": store_transactions,
        "incidents": incidents,
    }


def run_simulation(days: int) -> dict:
    daily_data = []
    all_incidents = []

    # Per-run modifiers — generated once, give each run a unique character.
    # Wide range so different rides/stores can credibly top the leaderboard.
    run_ride_mods = {r["name"]: random.uniform(0.30, 2.50) for r in RIDES}
    run_store_mods = {s["name"]: random.uniform(0.35, 2.20) for s in ALL_STORES}
    run_food_scale = random.uniform(0.65, 1.45)
    run_retail_scale = random.uniform(0.65, 1.45)

    cumulative_ride_riders = {r["name"]: 0 for r in RIDES}
    cumulative_ride_operating_hours = {r["name"]: 0 for r in RIDES}
    cumulative_store_revenue = {s["name"]: 0.0 for s in ALL_STORES}
    cumulative_ticket_counts = {"adult": 0, "child": 0, "toddler": 0, "senior": 0}
    archetype_totals = {a["name"]: 0 for a in ARCHETYPES}
    weather_stats = {
        "Sunny": {"count": 0, "total_attendance": 0, "total_revenue": 0.0},
        "Cloudy": {"count": 0, "total_attendance": 0, "total_revenue": 0.0},
        "Rainy": {"count": 0, "total_attendance": 0, "total_revenue": 0.0},
    }

    for day_num in range(1, days + 1):
        day = _simulate_day(day_num, run_ride_mods, run_store_mods, run_food_scale, run_retail_scale)
        daily_data.append(day)
        all_incidents.extend(day["incidents"])

        for ride_name, riders in day["ride_riders"].items():
            cumulative_ride_riders[ride_name] += riders
        for ride_name, op_hours in day["ride_operating_hours"].items():
            cumulative_ride_operating_hours[ride_name] += op_hours
        for store_name, rev in day["store_revenue"].items():
            cumulative_store_revenue[store_name] += rev
        for t_type, count in day["ticket_counts"].items():
            cumulative_ticket_counts[t_type] += count
        for arch_name, count in day["archetype_counts"].items():
            archetype_totals[arch_name] += count

        w = day["weather"]
        weather_stats[w]["count"] += 1
        weather_stats[w]["total_attendance"] += day["attendance"]
        weather_stats[w]["total_revenue"] += day["total_revenue"]

    ride_breakdown_hours = {r["name"]: 0 for r in RIDES}
    ride_breakdown_counts = {r["name"]: 0 for r in RIDES}
    for inc in all_incidents:
        ride_breakdown_hours[inc["ride"]] += inc["hours_down"]
        ride_breakdown_counts[inc["ride"]] += 1

    ride_stats = {}
    for ride in RIDES:
        total_op_hours = cumulative_ride_operating_hours[ride["name"]]
        total_capacity = max(1, ride["max_hourly_capacity"] * total_op_hours)
        total_riders = cumulative_ride_riders[ride["name"]]
        ride_stats[ride["name"]] = {
            "total_riders": total_riders,
            "total_capacity": total_capacity,
            "avg_utilization": round(total_riders / total_capacity, 4),
            "breakdown_count": ride_breakdown_counts[ride["name"]],
            "total_breakdown_hours": ride_breakdown_hours[ride["name"]],
            "max_hourly_capacity": ride["max_hourly_capacity"],
        }

    store_stats = {
        store["name"]: {
            "total_revenue": round(cumulative_store_revenue[store["name"]], 2),
            "category": store["category"],
        }
        for store in ALL_STORES
    }

    ticket_stats = {
        t_type: {
            "count": count,
            "revenue": round(count * TICKET_PRICES[t_type], 2),
        }
        for t_type, count in cumulative_ticket_counts.items()
    }

    total_attendance = sum(d["attendance"] for d in daily_data)
    total_ticket_revenue = sum(d["ticket_revenue"] for d in daily_data)
    total_food_revenue = sum(d["food_beverage_revenue"] for d in daily_data)
    total_retail_revenue = sum(d["retail_merchandise_revenue"] for d in daily_data)
    total_revenue = total_ticket_revenue + total_food_revenue + total_retail_revenue

    best_day = max(daily_data, key=lambda d: d["total_revenue"])
    worst_day = min(daily_data, key=lambda d: d["total_revenue"])
    most_popular_ride = max(cumulative_ride_riders, key=cumulative_ride_riders.get)
    top_grossing_store = max(cumulative_store_revenue, key=cumulative_store_revenue.get)

    weather_summary = {
        state: {
            "count": stats["count"],
            "avg_attendance": round(stats["total_attendance"] / stats["count"], 1) if stats["count"] else 0,
            "avg_revenue": round(stats["total_revenue"] / stats["count"], 2) if stats["count"] else 0.0,
        }
        for state, stats in weather_stats.items()
    }

    clean_daily_data = [
        {
            "day": d["day"],
            "day_of_week": d["day_of_week"],
            "weather": d["weather"],
            "attendance": d["attendance"],
            "ticket_revenue": d["ticket_revenue"],
            "food_beverage_revenue": d["food_beverage_revenue"],
            "retail_merchandise_revenue": d["retail_merchandise_revenue"],
            "total_revenue": d["total_revenue"],
            "avg_spend_per_visitor": d["avg_spend_per_visitor"],
            "archetype_counts": d["archetype_counts"],
            "ticket_counts": d["ticket_counts"],
            # Per-day detail needed for CSV/SQL export
            "ride_riders": d["ride_riders"],
            "ride_operating_hours": d["ride_operating_hours"],
            "store_revenue": d["store_revenue"],
            "store_transactions": d["store_transactions"],
        }
        for d in daily_data
    ]

    return {
        "summary": {
            "total_days": days,
            "total_attendance": total_attendance,
            "total_revenue": round(total_revenue, 2),
            "total_ticket_revenue": round(total_ticket_revenue, 2),
            "total_food_beverage_revenue": round(total_food_revenue, 2),
            "total_retail_merchandise_revenue": round(total_retail_revenue, 2),
            "best_day": {
                "day": best_day["day"],
                "day_of_week": best_day["day_of_week"],
                "weather": best_day["weather"],
                "attendance": best_day["attendance"],
                "revenue": best_day["total_revenue"],
            },
            "worst_day": {
                "day": worst_day["day"],
                "day_of_week": worst_day["day_of_week"],
                "weather": worst_day["weather"],
                "attendance": worst_day["attendance"],
                "revenue": worst_day["total_revenue"],
            },
            "most_popular_ride": most_popular_ride,
            "top_grossing_store": top_grossing_store,
            "archetype_totals": archetype_totals,
            "weather_summary": weather_summary,
        },
        "daily_data": clean_daily_data,
        "ride_stats": ride_stats,
        "store_stats": store_stats,
        "ticket_stats": ticket_stats,
        "weather_log": [{"day": d["day"], "weather": d["weather"]} for d in daily_data],
        "incidents": all_incidents,
    }
