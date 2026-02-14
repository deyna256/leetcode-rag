from loguru import logger

from domain.models.problem import Problem
from infrastructure.leetcode_client import LeetCodeClient
from infrastructure.parsers.errors import PaidProblemError


async def get_problem(slug: str) -> Problem:
    client = LeetCodeClient()
    data = await client.fetch_question_detail(slug)

    if data.get("isPaidOnly"):
        raise PaidProblemError(f"Premium problem: {slug}")

    tags = [t["name"] for t in (data.get("topicTags") or [])]

    solution = data.get("solution")
    editorial = solution.get("content") if solution else None

    problem = Problem(
        problem_id=int(data["questionFrontendId"]),
        slug=data["titleSlug"],
        title=data["title"],
        difficulty=data["difficulty"],
        tags=tags,
        statement=data.get("content") or "",
        editorial=editorial,
    )

    logger.info(f"Fetched problem {problem.problem_id}: {problem.title}")
    return problem
