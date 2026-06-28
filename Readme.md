# Document Processing Pipeline

Built a document processing pipeline that accepts user uploads, stores processing tasks in a database, executes analysis asynchronously using Celery and Redis, and exposes task status and results through a FastAPI backend. The project includes JWT authentication, Docker-based deployment, and persistent task tracking, demonstrating practical experience with distributed backend systems.

## Features

- JWT Authentication
- Async document processing via Celery task queue
- Redis as message broker
- Real-time task status tracking
- Text analysis: word count, sentence count, reading time, top words

## Architecture

```
User uploads document
        ↓
FastAPI saves task to PostgreSQL (status: pending)
        ↓
FastAPI sends task ID to Redis queue
        ↓
FastAPI returns task_id immediately to user
        ↓
Celery worker picks up task from Redis
        ↓
Celery processes document (word count, reading time, top words)
        ↓
Celery updates PostgreSQL (status: completed + results)
        ↓
User polls GET /tasks/{id} to retrieve results

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
```
