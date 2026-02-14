from pydantic import BaseModel


class ProblemRequest(BaseModel):
    slug: str


class ProblemResponse(BaseModel):
    problem_id: int
    slug: str
    title: str
    difficulty: str
    tags: list[str]
    statement: str
    editorial: str | None = None


class ErrorResponse(BaseModel):
    status_code: int
    detail: str
    error_type: str
