class LeetCodeError(Exception):
    pass


class ProblemNotFoundError(LeetCodeError):
    pass


class PaidProblemError(LeetCodeError):
    pass


class LeetCodeAPIError(LeetCodeError):
    pass
