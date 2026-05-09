import random

WEATHER_STATES = [
    {
        "state": "Sunny",
        "probability": 0.50,
        "attendance_multiplier": 1.2,
        "food_spend_multiplier": 1.0,
        "aqua_rush_demand_multiplier": 1.5,
        "aqua_rush_closed": False,
    },
    {
        "state": "Cloudy",
        "probability": 0.30,
        "attendance_multiplier": 1.0,
        "food_spend_multiplier": 1.0,
        "aqua_rush_demand_multiplier": 1.0,
        "aqua_rush_closed": False,
    },
    {
        "state": "Rainy",
        "probability": 0.20,
        "attendance_multiplier": 0.5,
        "food_spend_multiplier": 1.2,
        "aqua_rush_demand_multiplier": 0.0,
        "aqua_rush_closed": True,
    },
]

_WEATHER_BY_STATE = {w["state"]: w for w in WEATHER_STATES}
_STATES = [w["state"] for w in WEATHER_STATES]
_WEIGHTS = [w["probability"] for w in WEATHER_STATES]


def roll_weather() -> dict:
    chosen = random.choices(_STATES, weights=_WEIGHTS, k=1)[0]
    return _WEATHER_BY_STATE[chosen]
