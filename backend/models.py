from pydantic import BaseModel, Field
from typing import List
from enum import Enum

class Gender(str, Enum):
    MALE = "male"
    FEMALE = "female"

class Goal(str, Enum):
    LOSE = "lose weight"
    MAINTAIN = "maintain"
    GAIN = "gain muscle"

class ActivityLevel(str, Enum):
    SEDENTARY = "sedentary"
    LIGHT = "lightly active"
    MODERATE = "moderately active"
    VERY = "very active"
    EXTRA = "extra_active"

class Intensity(str, Enum):
    NONE = "none" 
    LOW = "low"
    MODERATE = "moderate" 
    HIGH = "high"
    VERY_HIGH = "very_high"

class UserActivity(BaseModel):
    hours: float
    intensity: Intensity

class UserProfile(BaseModel):
    age: int
    height: float # in cm
    weight: float # in kg
    
    gender: Gender
    daily_activity: ActivityLevel
    goal: Goal
    
    activities: List[UserActivity] = Field(default_factory=list)
    
    meal_amount: int = Field(..., ge=2, le=6)
    
    allergies: List[str] = Field(default_factory=list)
    text_input: str = ""
    generation_index: int = 0 # For tracking multiple generations