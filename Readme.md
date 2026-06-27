# Document Processing Pipeline

An async document processing API built with FastAPI, Celery, Redis, and PostgreSQL.

## Features

- JWT Authentication
- Async document processing via Celery task queue
- Redis as message broker
- Real-time task status tracking
- Text analysis: word count, sentence count, reading time, top words

## Tech Stack

- Python, FastAPI, Uvicorn
- Celery + Redis (async task queue)
- PostgreSQL + SQLAlchemy
- JWT via python-jose

## Setup

1. Clone the repo
2. Create and activate virtual environment
3. Install dependencies: `pip install -r requirements.txt`
4. Create `.env` file with your credentials
5. Start Redis server
6. Run migrations: tables created automatically on startup
7. Start server: `uvicorn app.main:app --reload`
8. Start Celery worker: `celery -A app.celery_app:celery_app worker --loglevel=info --pool=solo`

## API Endpoints

| Method | Endpoint           | Description                    |
| ------ | ------------------ | ------------------------------ |
| POST   | /register          | Register a new user            |
| POST   | /login             | Login and get JWT token        |
| POST   | /upload?token=     | Upload document for processing |
| GET    | /tasks/{id}?token= | Get task status and results    |
| GET    | /tasks?token=      | List all your tasks            |

## How It Works

User uploads a document → API saves task as "pending" and returns task_id immediately → Celery picks up the task from Redis → Processes the document in background → Updates task status to "completed" with results → User polls the status endpoint to retrieve results
