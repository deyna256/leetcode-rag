from .models import Chunk, Problem

MAX_CHUNK_LEN = 2000
OVERLAP = 200


def _split_text(text: str) -> list[str]:
    if len(text) <= MAX_CHUNK_LEN:
        return [text]
    parts = []
    start = 0
    while start < len(text):
        end = start + MAX_CHUNK_LEN
        parts.append(text[start:end])
        start = end - OVERLAP
    return parts


def chunk_problem(problem: Problem) -> list[Chunk]:
    chunks: list[Chunk] = []

    if problem.statement:
        for part in _split_text(problem.statement):
            chunks.append(
                Chunk(
                    problem_id=problem.problem_id,
                    title=problem.title,
                    difficulty=problem.difficulty,
                    tags=problem.tags,
                    chunk_type="statement",
                    text=part,
                )
            )

    if problem.editorial:
        for part in _split_text(problem.editorial):
            chunks.append(
                Chunk(
                    problem_id=problem.problem_id,
                    title=problem.title,
                    difficulty=problem.difficulty,
                    tags=problem.tags,
                    chunk_type="editorial",
                    text=part,
                )
            )

    return chunks
