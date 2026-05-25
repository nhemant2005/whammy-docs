# Todo App

A minimal REST API for managing a personal todo list, built with FastAPI.

## Features

- Create, read, update, and delete todos
- Mark todos as done
- In-memory storage (resets on restart)

## Quickstart

```bash
pip install -r requirements.txt
uvicorn main:app --reload
```

Visit `http://localhost:8000/docs` for the interactive API docs.

## Endpoints

| Method | Path             | Description        |
|--------|------------------|--------------------|
| GET    | /todos           | List all todos     |
| POST   | /todos           | Create a todo      |
| GET    | /todos/{id}      | Get one todo       |
| PUT    | /todos/{id}      | Update a todo      |
| DELETE | /todos/{id}      | Delete a todo      |

## Configuration

Copy `.env.example` to `.env` and adjust values.
