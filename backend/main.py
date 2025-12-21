from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel 


app = FastAPI()

# CORS middleware setup, at the moment allowing all origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Data model for user input
class UserProfile(BaseModel):
    age: int
    weight: float # in kg
    height: float # in m
    gender: str # 'male' or 'female'
    pal: float # Physical Activity Level
    allergies: list[str] = [] # List of allergies
    text_input: str = "" # Optional text input for additional preferences

@app.post("/generate-plan")
def generate_meal_plan(user: UserProfile):
    # Logic will go here
    return {"message": "Plan generation started"}
