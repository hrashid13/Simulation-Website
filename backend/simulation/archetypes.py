TICKET_PRICES = {
    "adult": 85.00,
    "child": 65.00,
    "toddler": 0.00,
    "senior": 70.00,
}

ARCHETYPES = [
    {
        "name": "Family with Young Kids",
        "weight": 0.25,
        "group_size_range": (3, 6),
        "ticket_mix": {"adult": 2, "child": 2, "toddler": 1},
        "ticket_mix_variable": False,
        "ride_preferences": ["Carousel", "Mini Coaster", "Bumper Cars", "Haunted Mansion"],
        "ride_aversions": ["Thunderbolt", "Free Fall Tower"],
        "food_spend_multiplier": 1.8,
        "merch_spend_multiplier": 1.5,
        "hours_in_park_range": (6, 9),
        "arrival_window": (9, 12),
        "weekday_only": False,
    },
    {
        "name": "Thrill Seekers",
        "weight": 0.15,
        "group_size_range": (2, 3),
        "ticket_mix": {"adult": "all"},
        "ticket_mix_variable": True,
        "ride_preferences": ["Thunderbolt", "Free Fall Tower", "Aqua Rush"],
        "ride_aversions": ["Carousel", "Mini Coaster"],
        "food_spend_multiplier": 0.7,
        "merch_spend_multiplier": 0.6,
        "hours_in_park_range": (8, 12),
        "arrival_window": (10, 13),
        "weekday_only": False,
    },
    {
        "name": "Teenage Group",
        "weight": 0.20,
        "group_size_range": (4, 6),
        "ticket_mix": {"adult": "all"},
        "ticket_mix_variable": True,
        "ride_preferences": ["Thunderbolt", "Free Fall Tower", "Bumper Cars", "Aqua Rush"],
        "ride_aversions": ["Carousel", "Mini Coaster"],
        "food_spend_multiplier": 0.9,
        "merch_spend_multiplier": 1.2,
        "hours_in_park_range": (7, 11),
        "arrival_window": (11, 14),
        "weekday_only": False,
    },
    {
        "name": "Couple / Date",
        "weight": 0.20,
        "group_size_range": (2, 2),
        "ticket_mix": {"adult": 2},
        "ticket_mix_variable": False,
        "ride_preferences": ["Haunted Mansion", "Aqua Rush", "Thunderbolt", "Carousel"],
        "ride_aversions": ["Mini Coaster"],
        "food_spend_multiplier": 1.2,
        "merch_spend_multiplier": 1.8,
        "hours_in_park_range": (5, 8),
        "arrival_window": (11, 15),
        "weekday_only": False,
    },
    {
        "name": "Senior Group",
        "weight": 0.10,
        "group_size_range": (2, 4),
        "ticket_mix": {"senior": "all"},
        "ticket_mix_variable": True,
        "ride_preferences": ["Carousel", "Haunted Mansion", "Bumper Cars"],
        "ride_aversions": ["Thunderbolt", "Free Fall Tower", "Aqua Rush"],
        "food_spend_multiplier": 1.5,
        "merch_spend_multiplier": 1.3,
        "hours_in_park_range": (4, 7),
        "arrival_window": (9, 11),
        "weekday_only": False,
    },
    {
        "name": "School / Large Group",
        "weight": 0.10,
        "group_size_range": (10, 25),
        "ticket_mix": {"adult": 2, "child": "rest"},
        "ticket_mix_variable": True,
        "ride_preferences": ["Carousel", "Mini Coaster", "Bumper Cars", "Haunted Mansion"],
        "ride_aversions": ["Free Fall Tower"],
        "food_spend_multiplier": 1.1,
        "merch_spend_multiplier": 0.8,
        "hours_in_park_range": (6, 8),
        "arrival_window": (9, 10),
        "weekday_only": True,
    },
]

WEEKDAY_ARCHETYPES = [a for a in ARCHETYPES if not a["weekday_only"]]

def get_weekend_weights():
    total_weekday_weight = sum(a["weight"] for a in WEEKDAY_ARCHETYPES)
    scale = 1.0 / total_weekday_weight
    return [a["weight"] * scale for a in WEEKDAY_ARCHETYPES]

def get_weekday_weights():
    return [a["weight"] for a in ARCHETYPES]
