from litestar import Controller, post
from litestar.status_codes import HTTP_200_OK
from loguru import logger

from api.schemas import ProblemRequest, ProblemResponse
from services.problem import get_problem


class ProblemController(Controller):
    path = "/problem"

    @post("/", status_code=HTTP_200_OK)
    async def fetch_problem(self, data: ProblemRequest) -> ProblemResponse:
        logger.debug(f"API request for problem slug: {data.slug}")

        problem = await get_problem(data.slug)

        return ProblemResponse(
            problem_id=problem.problem_id,
            slug=problem.slug,
            title=problem.title,
            difficulty=problem.difficulty,
            tags=problem.tags,
            statement=problem.statement,
            editorial=problem.editorial,
        )
