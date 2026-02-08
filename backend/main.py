from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from models import UserProfile
from plan_generator import MealPlanGenerator
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi import Request

app = FastAPI()

# Enable CORS for Frontend Access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"status": "API is running"}

@app.post("/generate-plan")
def generate_meal_plan(user: UserProfile, use_ai: bool = True):
    """
    Generates a meal plan based on user profile.
    
    Args:
    - user: The UserProfile data from frontend.
    - use_ai: If true, sends result to Gemini for pretty formatting. 
              If false, returns raw data (faster).
    """
    try:
        # 1. Initializes generator
        # This will fetch data from Supabase (make sure .env is set)
        generator = MealPlanGenerator(user)
        
        # 2. Generates raw meal plan using KNN and rules engine
        raw_plan = generator.generate_raw_plan()
        
        # 3. (Optional) Enrich with Gemini AI
        if use_ai:
            final_plan = generator.enrich_with_gemini(raw_plan)
            
            if final_plan:
                return final_plan
            else:
                # Fallback if Gemini fails
                return {"status": "partial_success", "message": "AI generation failed, returning raw data", "data": raw_plan}
        
        # 4. Returns Raw Data
        return raw_plan

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    # Gets the raw body to see what was sent
    body = await request.body()
    
    # Printing the exact error details to your terminal
    print(f"\nVALIDATION ERROR:")
    print(f"Received Body: {body.decode()}")
    print(f"Errors: {exc.errors()}\n")
    
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors()},
    )