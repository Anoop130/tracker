#!/usr/bin/env python3
"""
FastAPI main application for AI-Powered Nutrition Coach
"""
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import uvicorn
import os
from dotenv import load_dotenv

# Import existing modules
import sys
sys.path.append('..')
from app.llm import chat_once, estimate_food
from db import api
from database import (
    init_database, get_user_foods, add_user_food, 
    get_user_goals, set_user_goals, get_user_daily_summary, get_connection
)

load_dotenv()

# Initialize FastAPI app
app = FastAPI(
    title="AI-Powered Nutrition Coach API",
    description="Full-stack nutrition tracking platform with LLM integration",
    version="1.0.0"
)

# CORS middleware for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001", "http://localhost:5173"],  # React dev servers
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()

# Pydantic models
class UserLogin(BaseModel):
    email: str
    password: str

class UserRegister(BaseModel):
    email: str
    password: str

class FoodItem(BaseModel):
    name: str
    serving_desc: str
    cal: float
    protein: float
    carbs: float
    fat: float
    provenance: Optional[str] = "user"

class MealItem(BaseModel):
    name: str
    qty: float

class LogMealRequest(BaseModel):
    items: List[MealItem]
    date: Optional[str] = None

class SetGoalRequest(BaseModel):
    calories: float
    protein_g: float
    carbs_g: float
    fat_g: float

class ChatMessage(BaseModel):
    message: str
    history: Optional[List[Dict[str, str]]] = []

class ChatResponse(BaseModel):
    speak: str
    actions: List[Dict[str, Any]]
    sql_commands: List[Dict[str, Any]] = []

# Security scheme
security = HTTPBearer()

# Authentication dependency (simplified for now)
def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    # For now, just return a mock user_id
    # In production, validate JWT token
    return {"user_id": 1, "email": "demo@example.com"}

# Health check endpoint
@app.get("/")
async def root():
    return {"message": "AI-Powered Nutrition Coach API", "status": "running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": "1.0.0"}

# Authentication endpoints
@app.post("/api/auth/login")
async def login(user: UserLogin):
    # Simplified authentication for demo
    if user.email == "demo@example.com" and user.password == "demo123":
        return {"token": "demo_token_123", "user": {"id": 1, "email": user.email}}
    raise HTTPException(status_code=401, detail="Invalid credentials")

@app.post("/api/auth/register")
async def register(user: UserRegister):
    # Simplified registration for demo
    return {"token": "demo_token_123", "user": {"id": 1, "email": user.email}}

# Food management endpoints
@app.get("/api/foods")
async def get_foods(search: Optional[str] = None, current_user: dict = Depends(get_current_user)):
    """Get list of foods, optionally filtered by search term"""
    try:
        foods = get_user_foods(current_user["user_id"], search)
        return foods
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/foods")
async def add_food(food: FoodItem, current_user: dict = Depends(get_current_user)):
    """Add a new food item to the database"""
    try:
        food_id = add_user_food(
            current_user["user_id"],
            food.name, 
            food.serving_desc, 
            food.cal, 
            food.protein, 
            food.carbs, 
            food.fat, 
            food.provenance
        )
        return {"success": True, "message": "Food added successfully", "food_id": food_id}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Meal logging endpoints
@app.post("/api/meals")
async def log_meal(meal: LogMealRequest, current_user: dict = Depends(get_current_user)):
    """Log a meal with multiple food items"""
    try:
        # Convert to the format expected by existing function
        items = [{"name": item.name, "qty": item.qty} for item in meal.items]
        
        # Use existing log_meal logic
        from app.main import _log_meal_with_estimates
        _log_meal_with_estimates({"items": items, "date": meal.date})
        
        return {"success": True, "message": "Meal logged successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Nutrition summary endpoint
@app.get("/api/summary")
async def get_daily_summary(date: Optional[str] = None, current_user: dict = Depends(get_current_user)):
    """Get daily nutrition summary"""
    try:
        from datetime import date as dt
        if not date:
            date = dt.today().isoformat()
        summary = get_user_daily_summary(current_user["user_id"], date)
        return summary
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Goals management endpoint
@app.post("/api/goals")
async def set_goal(goal: SetGoalRequest, current_user: dict = Depends(get_current_user)):
    """Set nutrition goals"""
    try:
        set_user_goals(current_user["user_id"], goal.calories, goal.protein_g, goal.carbs_g, goal.fat_g)
        return {"success": True, "message": "Goals set successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/goals")
async def get_goals(current_user: dict = Depends(get_current_user)):
    """Get current nutrition goals"""
    try:
        goals = get_user_goals(current_user["user_id"])
        if goals:
            return goals
        else:
            # Return default goals if none set
            return {
                "calories": 2000,
                "protein_g": 150,
                "carbs_g": 200,
                "fat_g": 80
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# LLM Chat endpoint
@app.post("/api/chat", response_model=ChatResponse)
async def chat_with_llm(chat: ChatMessage, current_user: dict = Depends(get_current_user)):
    """Chat with the nutrition coach LLM"""
    try:
        # Add user message to history
        history = chat.history + [{"role": "user", "content": chat.message}]
        
        # Get LLM response
        raw_response = chat_once(history)
        
        # Parse the response using existing logic
        import sys
        sys.path.append('..')
        from app.main import parse_turn, generate_sql_commands
        parsed = parse_turn(raw_response)
        
        # Generate and execute SQL commands based on validated actions
        sql_commands = generate_sql_commands(parsed["actions"])
        sql_results = []
        for sql_cmd in sql_commands:
            try:
                with get_connection() as conn:
                    conn.execute(sql_cmd["sql"])
                    conn.commit()
                sql_results.append({"success": True, "description": sql_cmd.get("description", "")})
            except Exception as e:
                sql_results.append({"success": False, "error": str(e), "description": sql_cmd.get("description", "")})
        
        return ChatResponse(
            speak=parsed["speak"],
            actions=parsed["actions"],
            sql_commands=sql_results
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LLM error: {str(e)}")

# Food estimation endpoint
@app.post("/api/foods/estimate")
async def estimate_food_nutrition(name: str, current_user: dict = Depends(get_current_user)):
    """Get nutrition estimation for a food item using LLM"""
    try:
        raw_response = estimate_food(name)
        from app.main import parse_turn
        parsed = parse_turn(raw_response)
        return parsed
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Estimation error: {str(e)}")

if __name__ == "__main__":
    # Initialize database schema
    init_database()
    
    # Run the server
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
