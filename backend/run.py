#!/usr/bin/env python3
"""
Startup script for the FastAPI backend
"""
import uvicorn
from database import init_database

if __name__ == "__main__":
    # Initialize database
    print("Initializing database...")
    init_database()
    print("Database initialized!")
    
    # Start the server
    print("Starting FastAPI server...")
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
