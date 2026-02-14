from .chunker import chunk_problem
from .db import qdrant_upsert_chunks, upsert_problem
from .embedder import embed_texts
from .models import ParserProblem, Problem


async def index_problem(pp: ParserProblem) -> int:
    problem = Problem(
        problem_id=pp.problem_id,
        slug=pp.slug,
        title=pp.title,
        difficulty=pp.difficulty,
        tags=pp.tags,
        statement=pp.statement or None,
        editorial=pp.editorial or None,
        url=f"https://leetcode.com/problems/{pp.slug}/",
    )
    await upsert_problem(problem)

    chunks = chunk_problem(problem)
    if chunks:
        texts = [c.text for c in chunks]
        vectors = embed_texts(texts)
        qdrant_upsert_chunks(chunks, vectors)

    return problem.problem_id
