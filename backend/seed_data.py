#!/usr/bin/env python3
"""
Seed the database with common foods for testing
"""
from database import get_connection, add_user_food

def seed_foods():
    """Add common foods to the database"""
    foods = [
        {
            "name": "egg",
            "serving_desc": "1 large",
            "cal": 70,
            "protein": 6,
            "carbs": 0.6,
            "fat": 5,
            "provenance": "seed"
        },
        {
            "name": "chicken breast",
            "serving_desc": "100g cooked",
            "cal": 165,
            "protein": 31,
            "carbs": 0,
            "fat": 3.6,
            "provenance": "seed"
        },
        {
            "name": "rice",
            "serving_desc": "1 cup cooked",
            "cal": 206,
            "protein": 4.3,
            "carbs": 45,
            "fat": 0.4,
            "provenance": "seed"
        },
        {
            "name": "leg quarter",
            "serving_desc": "1 piece (100g)",
            "cal": 200,
            "protein": 25,
            "carbs": 0,
            "fat": 11,
            "provenance": "seed"
        },
        {
            "name": "bread",
            "serving_desc": "1 slice",
            "cal": 80,
            "protein": 3,
            "carbs": 15,
            "fat": 1,
            "provenance": "seed"
        },
        {
            "name": "milk",
            "serving_desc": "1 cup",
            "cal": 150,
            "protein": 8,
            "carbs": 12,
            "fat": 8,
            "provenance": "seed"
        }
    ]
    
    print("Seeding database with common foods...")
    for food in foods:
        try:
            food_id = add_user_food(
                user_id=1,
                name=food["name"],
                serving_desc=food["serving_desc"],
                cal=food["cal"],
                protein=food["protein"],
                carbs=food["carbs"],
                fat=food["fat"],
                provenance=food["provenance"]
            )
            print(f"Added {food['name']} (ID: {food_id})")
        except Exception as e:
            print(f"Error adding {food['name']}: {e}")
    
    print("Database seeding complete!")

if __name__ == "__main__":
    seed_foods()
