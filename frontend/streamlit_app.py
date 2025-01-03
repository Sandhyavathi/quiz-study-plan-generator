import streamlit as st
import requests
import json

# API URLs
ROOT_API_URL = "http://127.0.0.1:8000/"  # Replace with your FastAPI root endpoint
QUIZ_API_URL = "http://127.0.0.1:8000/quiz"  # Replace with your FastAPI quiz endpoint
CHECK_ANSWERS_API_URL = "http://127.0.0.1:8000/check_answers"  # Replace with your FastAPI check answers endpoint

# Initialize session state
if "quiz_data" not in st.session_state:
    st.session_state.quiz_data = []
if "user_answers" not in st.session_state:
    st.session_state.user_answers = {}
if "available_topics" not in st.session_state:
    st.session_state.available_topics = []

# Function to fetch available topics
def fetch_available_topics():
    try:
        response = requests.get(ROOT_API_URL)
        response.raise_for_status()
        return response.json().get("available_topics", [])
    except requests.exceptions.RequestException as e:
        st.error(f"Failed to load topics: {e}")
        return []

# Function to fetch quiz questions based on the selected topic
def fetch_quiz_questions(selected_topics):
    try:
        response = requests.get(QUIZ_API_URL, params={"topics": selected_topics})
        response.raise_for_status()
        return response.json().get("questions", [])
    except requests.exceptions.RequestException as e:
        st.error(f"Failed to load quiz questions: {e}")
        return []

# Function to submit answers and fetch results
def submit_answers(user_answers):
    try:
        response = requests.post(
            CHECK_ANSWERS_API_URL,
            headers={"Content-Type": "application/json"},
            data=json.dumps(user_answers),
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Failed to submit answers: {e}")
        return None

# Fetch available topics at startup
if not st.session_state.available_topics:
    st.session_state.available_topics = fetch_available_topics()

# Title for the app
st.title("Interactive Quiz and Study Plan Generator")

# Select topics
st.header("Select Topics")
selected_topic = st.selectbox(
    "Choose a topic to start the quiz:",
    options=st.session_state.available_topics,
)

# Fetch quiz questions when a topic is selected
if st.button("Start Quiz"):
    if selected_topic:
        st.session_state.quiz_data = fetch_quiz_questions(selected_topics=[selected_topic])
        st.session_state.user_answers = {}  # Reset user answers for the new quiz

# Display quiz questions
if st.session_state.quiz_data:
    st.header("Take the Quiz")
    for question in st.session_state.quiz_data:
        question_id = question["id"]
        st.subheader(f"Q: {question['question']}")
        selected_option = st.radio(
            f"Choose your answer for question {question_id}:",
            options=enumerate(question["options"], 1),
            format_func=lambda x: x[1],
            key=f"question_{question_id}",
            index=st.session_state.user_answers.get(question_id, -1) - 1
            if question_id in st.session_state.user_answers
            else 0,
        )
        # Save the answer in session state
        st.session_state.user_answers[question_id] = selected_option[0]

    # Submit answers and display results
    if st.button("Submit Answers"):
        user_answers = [
            {"id": q_id, "answer": answer}
            for q_id, answer in st.session_state.user_answers.items()
        ]
        results = submit_answers(user_answers)

        if results:
            incorrect_answers = results.get("incorrect_answers", [])
            study_plans = results.get("study_plans", [])

            # Display incorrect answers
            if incorrect_answers:
                st.header("Review Your Incorrect Answers")
                for question in incorrect_answers:
                    st.error(
                        f"Q{question['id']}: {question['question']}\n"
                        f"**Correct Answer**: {question['options'][question['correctAnswer'] - 1]}\n"
                        f"**Topic**: {question['topic']}"
                    )

                # Display generated study plans
                st.header("Generated Study Plans")
                for plan in study_plans:
                    for topic, study_plan in plan.items():
                        st.subheader(f"Study Plan for {topic}")
                        st.write(study_plan)
            else:
                st.success("Great job! All your answers are correct.")
        else:
            st.error("An error occurred while processing your answers.")
else:
    st.warning("No quiz questions available. Please select a topic and start the quiz.")

