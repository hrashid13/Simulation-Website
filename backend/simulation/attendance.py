import random

BASE_ATTENDANCE_MIN = 2000
BASE_ATTENDANCE_MAX = 5000
WEEKEND_MULTIPLIER = 1.4
WEEKDAY_MULTIPLIER = 1.0
VARIANCE = 0.10

DAYS_OF_WEEK = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


def get_day_of_week(day_number: int) -> str:
    return DAYS_OF_WEEK[(day_number - 1) % 7]


def is_weekend(day_of_week: str) -> bool:
    return day_of_week in ("Saturday", "Sunday")


def calculate_attendance(day_number: int, weather_multiplier: float) -> tuple:
    day_of_week = get_day_of_week(day_number)
    base = random.randint(BASE_ATTENDANCE_MIN, BASE_ATTENDANCE_MAX)
    dow_multiplier = WEEKEND_MULTIPLIER if is_weekend(day_of_week) else WEEKDAY_MULTIPLIER
    variance = 1.0 + random.uniform(-VARIANCE, VARIANCE)
    attendance = int(base * weather_multiplier * dow_multiplier * variance)
    return attendance, day_of_week
