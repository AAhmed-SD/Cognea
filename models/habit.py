from pydantic import BaseModel


class Habit(BaseModel):
    id: int
    name: str
    description: str | None = None
    user_id: int
    is_active: bool = True
