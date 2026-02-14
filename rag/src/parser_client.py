import httpx

from .config import settings
from .models import ParserProblem


async def fetch_problem(slug: str) -> ParserProblem:
    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(
            f"{settings.PARSER_BASE_URL}/problem",
            json={"slug": slug},
        )
        resp.raise_for_status()
        return ParserProblem.model_validate(resp.json())
