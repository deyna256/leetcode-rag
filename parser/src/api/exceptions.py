from litestar import Request, Response
from litestar.status_codes import (
    HTTP_403_FORBIDDEN,
    HTTP_404_NOT_FOUND,
    HTTP_500_INTERNAL_SERVER_ERROR,
    HTTP_502_BAD_GATEWAY,
)
from loguru import logger

from api.schemas import ErrorResponse
from infrastructure.parsers.errors import (
    LeetCodeAPIError,
    PaidProblemError,
    ProblemNotFoundError,
)


def exception_to_http_response(request: Request, exc: Exception) -> Response[ErrorResponse]:
    logger.error(f"Exception in {request.url}: {exc}")

    if isinstance(exc, ProblemNotFoundError):
        status_code = HTTP_404_NOT_FOUND
        error_type = "ProblemNotFoundError"
        detail = str(exc)

    elif isinstance(exc, PaidProblemError):
        status_code = HTTP_403_FORBIDDEN
        error_type = "PaidProblemError"
        detail = str(exc)

    elif isinstance(exc, LeetCodeAPIError):
        status_code = HTTP_502_BAD_GATEWAY
        error_type = "LeetCodeAPIError"
        detail = str(exc)

    else:
        logger.exception(f"Unexpected error: {exc}")
        status_code = HTTP_500_INTERNAL_SERVER_ERROR
        error_type = type(exc).__name__
        detail = "An unexpected error occurred"

    error_response = ErrorResponse(
        status_code=status_code,
        detail=detail,
        error_type=error_type,
    )

    return Response(
        content=error_response,
        status_code=status_code,
    )
