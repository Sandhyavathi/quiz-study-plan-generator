import os
import sys
import json
import random
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional

# Debug: Print sys.path
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../"))
sys.path.append(BASE_DIR)
print("Python sys.path:", sys.path)

# Ensure cohere_api is correctly imported from app.study_plan_generator
try:
    from app.study_plan_generator.cohere_api import generate_study_plan
except ImportError as e:
    raise HTTPException(status_code=500, detail=f"Failed to import generate_study_plan: {e}")

# Initialize FastAPI app
app = FastAPI()

# Path to the questions JSON file
QUESTIONS_FILE_PATH = os.path.join(os.path.dirname(__file__), "questions.json")


def get_topics():
    """
    Get the list of unique topics from the JSON file.
    """
    if not os.path.exists(QUESTIONS_FILE_PATH):
        raise HTTPException(status_code=500, detail="Questions JSON file not found.")
        
    with open(QUESTIONS_FILE_PATH) as f:
        questions = json.load(f)
        topics = list({q["topic"] for q in questions})  # Get unique topics
        return topics


def get_random_questions(selected_topics: Optional[List[str]] = None, max_questions: int = 20):
    """
    Fetch random questions based on selected topics or fetch all topics if "All Topics" is chosen.
    """
    if not os.path.exists(QUESTIONS_FILE_PATH):
        raise HTTPException(status_code=500, detail="Questions JSON file not found.")

    with open(QUESTIONS_FILE_PATH) as f:
        questions = json.load(f)
        if selected_topics and "All Topics" not in selected_topics:
            # Filter questions by selected topics
            questions = [q for q in questions if q["topic"] in selected_topics]
        random.shuffle(questions)  # Shuffle the questions
        return questions[:max_questions]


# Define the root route with available topics
@app.get("/")
def read_root():
    try:
        topics = get_topics()
    except HTTPException as e:
        raise e  # Reraise HTTPException
    return {
        "message": "Welcome to the Quiz-Based Study Plan Generator!",
        "available_topics": topics + ["All Topics"],  # Add "All Topics" as an option
    }


# Endpoint to serve quiz questions
@app.get("/quiz")
def get_quiz(topics: List[str] = Query(None, description="Topics to test on")):
    if not topics:
        raise HTTPException(status_code=400, detail="No topics selected.")
    
    try:
        questions = get_random_questions(selected_topics=topics)
    except HTTPException as e:
        raise e  # Reraise HTTPException

    return {"questions": questions}


# Define the Pydantic model for incoming user answers
class UserAnswer(BaseModel):
    id: int
    answer: int


@app.post("/check_answers")
def check_answers(user_answers: List[UserAnswer]):
    """
    Check answers, identify incorrect ones, and generate study plans.
    """
    if not os.path.exists(QUESTIONS_FILE_PATH):
        raise HTTPException(status_code=500, detail="Questions JSON file not found.")
    
    with open(QUESTIONS_FILE_PATH) as f:
        questions = json.load(f)

    incorrect_answers = []
    for user_answer in user_answers:
        question = next((q for q in questions if q["id"] == user_answer.id), None)
        if question and question["correctAnswer"] != user_answer.answer:
            incorrect_answers.append(question)

    # Generate a study plan for incorrect answers
    if incorrect_answers:
        try:
            incorrect_topics = {q["topic"] for q in incorrect_answers}  # Unique topics
            study_plans = []
            for topic in incorrect_topics:
                study_plan = generate_study_plan(topic)  # Call external function to generate the plan
                study_plans.append({topic: study_plan})
            return {
                "incorrect_answers": incorrect_answers,
                "study_plans": study_plans,
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error generating study plan: {e}")

    return {
        "incorrect_answers": [],
        "study_plans": "No incorrect answers, no study plan needed.",
    }

