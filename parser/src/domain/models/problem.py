from dataclasses import dataclass, field


@dataclass
class Problem:
    problem_id: int
    slug: str
    title: str
    difficulty: str
    tags: list[str] = field(default_factory=list)
    statement: str = ""
    editorial: str | None = None
