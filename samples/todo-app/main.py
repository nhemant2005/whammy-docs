from fastapi import FastAPI, HTTPException
from database import db
from schemas import TodoCreate, TodoUpdate, TodoOut

app = FastAPI(title="Todo App", description="Simple todo list API")


@app.get("/todos", response_model=list[TodoOut])
def list_todos():
    return list(db.values())


@app.post("/todos", response_model=TodoOut, status_code=201)
def create_todo(body: TodoCreate):
    todo_id = db["_next_id"]
    db["_next_id"] += 1
    todo = {"id": todo_id, "title": body.title, "done": False}
    db[todo_id] = todo
    return todo


@app.get("/todos/{todo_id}", response_model=TodoOut)
def get_todo(todo_id: int):
    if todo_id not in db:
        raise HTTPException(status_code=404, detail="Todo not found")
    return db[todo_id]


@app.put("/todos/{todo_id}", response_model=TodoOut)
def update_todo(todo_id: int, body: TodoUpdate):
    if todo_id not in db:
        raise HTTPException(status_code=404, detail="Todo not found")
    todo = db[todo_id]
    if body.title is not None:
        todo["title"] = body.title
    if body.done is not None:
        todo["done"] = body.done
    return todo


@app.delete("/todos/{todo_id}", status_code=204)
def delete_todo(todo_id: int):
    if todo_id not in db:
        raise HTTPException(status_code=404, detail="Todo not found")
    del db[todo_id]
