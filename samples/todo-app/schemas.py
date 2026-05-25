from pydantic import BaseModel


class TodoCreate(BaseModel):
    title: str


class TodoUpdate(BaseModel):
    title: str | None = None
    done: bool | None = None


class TodoOut(BaseModel):
    id: int
    title: str
    done: bool
