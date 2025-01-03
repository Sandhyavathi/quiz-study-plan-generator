# Use the official Python image as a base image
FROM python:3.12-slim

# Set the working directory inside the container
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire app into the container
COPY . .

# Expose the port that FastAPI will run on
EXPOSE 8000

# Run the application using Uvicorn
CMD ["uvicorn", "app.quiz_backend.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

