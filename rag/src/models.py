from pydantic import BaseModel


class ParserProblem(BaseModel):
    problem_id: int
    slug: str
    title: str
    difficulty: str
    tags: list[str] = []
    statement: str = ""
    editorial: str | None = None


class Problem(BaseModel):
    problem_id: int
    slug: str
    title: str
    difficulty: str
    tags: list[str] = []
    statement: str | None = None
    editorial: str | None = None
    url: str | None = None


class LoadProblemRequest(BaseModel):
    slug: str


class SearchRequest(BaseModel):
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "query": "find two numbers that add up to target",
                    "limit": 10,
                }
            ]
        }
    }

    query: str
    difficulty: str | None = None
    tags: list[str] | None = None
    chunk_type: str | None = None
    limit: int = 10


class SearchResult(BaseModel):
    problem_id: int
    title: str
    difficulty: str
    tags: list[str] = []
    score: float
    snippet: str


class ProblemListItem(BaseModel):
    problem_id: int
    slug: str
    title: str
    difficulty: str
    tags: list[str] = []
    url: str | None = None


class Chunk(BaseModel):
    problem_id: int
    title: str
    difficulty: str
    tags: list[str] = []
    chunk_type: str
    text: str
