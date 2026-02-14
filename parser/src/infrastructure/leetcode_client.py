import httpx
from loguru import logger

from infrastructure.parsers.errors import LeetCodeAPIError, ProblemNotFoundError

LEETCODE_GRAPHQL_URL = "https://leetcode.com/graphql"

QUESTION_DETAIL_QUERY = """
query($titleSlug: String!) {
  question(titleSlug: $titleSlug) {
    questionFrontendId
    title
    titleSlug
    difficulty
    content
    isPaidOnly
    topicTags { name slug }
    solution { content }
  }
}
"""

QUESTION_LIST_QUERY = """
query($limit: Int, $skip: Int) {
  problemsetQuestionListV2(limit: $limit, skip: $skip) {
    totalLength
    questions {
      questionFrontendId
      title
      titleSlug
      difficulty
      paidOnly
      topicTags { name }
    }
  }
}
"""


class LeetCodeClient:
    def __init__(self) -> None:
        self._headers = {
            "Content-Type": "application/json",
            "Referer": "https://leetcode.com",
        }

    async def _graphql(self, query: str, variables: dict) -> dict:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                LEETCODE_GRAPHQL_URL,
                json={"query": query, "variables": variables},
                headers=self._headers,
            )
            resp.raise_for_status()
            data = resp.json()

        if "errors" in data:
            errors = data["errors"]
            logger.error(f"GraphQL errors: {errors}")
            raise LeetCodeAPIError(f"GraphQL errors: {errors}")

        return data["data"]

    async def fetch_question_detail(self, slug: str) -> dict:
        logger.debug(f"Fetching question detail: {slug}")
        data = await self._graphql(QUESTION_DETAIL_QUERY, {"titleSlug": slug})
        question = data.get("question")
        if question is None:
            raise ProblemNotFoundError(f"Problem not found: {slug}")
        return question

    async def fetch_question_list(self, skip: int = 0, limit: int = 50) -> dict:
        logger.debug(f"Fetching question list: skip={skip}, limit={limit}")
        data = await self._graphql(QUESTION_LIST_QUERY, {"skip": skip, "limit": limit})
        return data["problemsetQuestionListV2"]
