FOOD_AND_BEVERAGE = [
    {
        "name": "Main Street Grill",
        "category": "food_beverage",
        "avg_transaction_value": 18.00,
        "max_hourly_customers": 150,
    },
    {
        "name": "Pizza Place",
        "category": "food_beverage",
        "avg_transaction_value": 14.00,
        "max_hourly_customers": 200,
    },
    {
        "name": "Ice Cream Stand",
        "category": "food_beverage",
        "avg_transaction_value": 8.00,
        "max_hourly_customers": 300,
    },
    {
        "name": "Funnel Cake Cart",
        "category": "food_beverage",
        "avg_transaction_value": 7.00,
        "max_hourly_customers": 250,
    },
    {
        "name": "Burger Shack",
        "category": "food_beverage",
        "avg_transaction_value": 16.00,
        "max_hourly_customers": 180,
    },
    {
        "name": "Snack Bar",
        "category": "food_beverage",
        "avg_transaction_value": 9.00,
        "max_hourly_customers": 350,
    },
    {
        "name": "Lemonade Stand",
        "category": "food_beverage",
        "avg_transaction_value": 5.00,
        "max_hourly_customers": 400,
    },
]

RETAIL_AND_MERCHANDISE = [
    {
        "name": "Souvenir Shop",
        "category": "retail_merchandise",
        "avg_transaction_value": 22.00,
        "max_hourly_customers": 120,
    },
    {
        "name": "Photo Shop",
        "category": "retail_merchandise",
        "avg_transaction_value": 35.00,
        "max_hourly_customers": 80,
    },
    {
        "name": "Toy and Games Store",
        "category": "retail_merchandise",
        "avg_transaction_value": 28.00,
        "max_hourly_customers": 100,
    },
    {
        "name": "Apparel Store",
        "category": "retail_merchandise",
        "avg_transaction_value": 45.00,
        "max_hourly_customers": 90,
    },
    {
        "name": "Arcade",
        "category": "retail_merchandise",
        "avg_transaction_value": 15.00,
        "max_hourly_customers": 200,
    },
]

ALL_STORES = FOOD_AND_BEVERAGE + RETAIL_AND_MERCHANDISE
STORE_NAMES = [s["name"] for s in ALL_STORES]
