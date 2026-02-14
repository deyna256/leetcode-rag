from litestar import Litestar
from litestar.openapi.config import OpenAPIConfig

from api.exceptions import exception_to_http_response
from api.routes import ProblemController
from infrastructure.parsers.errors import (
    LeetCodeAPIError,
    PaidProblemError,
    ProblemNotFoundError,
)


def create_app() -> Litestar:
    exception_handlers = {
        ProblemNotFoundError: exception_to_http_response,
        PaidProblemError: exception_to_http_response,
        LeetCodeAPIError: exception_to_http_response,
    }

    openapi_config = OpenAPIConfig(
        title="LeetCode Problem Parser API",
        version="1.0.0",
        description="API for fetching LeetCode problem details via GraphQL",
    )

    app = Litestar(
        route_handlers=[ProblemController],
        exception_handlers=exception_handlers,
        openapi_config=openapi_config,
    )

    return app


app = create_app()
