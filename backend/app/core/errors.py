class AppError(Exception):
    """Base class for errors that map onto a specific HTTP response."""

    status_code = 500
    message = "Unexpected server error"

    def __init__(self, message: str | None = None):
        super().__init__(message or self.message)
        if message:
            self.message = message


class NotFoundError(AppError):
    status_code = 404
    message = "Resource not found"


class DuplicateError(AppError):
    status_code = 409
    message = "Resource already exists"


class ValidationError(AppError):
    status_code = 422
    message = "Invalid request"


class GitHubError(AppError):
    status_code = 502
    message = "GitHub request failed"


class RepositoryNotFoundOnGitHub(GitHubError):
    status_code = 404
    message = "Repository not found on GitHub"


class RateLimitedError(GitHubError):
    status_code = 429
    message = "GitHub API rate limit reached"

    def __init__(self, message: str | None = None, reset_at: str | None = None):
        super().__init__(message)
        self.reset_at = reset_at


class UpstreamUnavailableError(GitHubError):
    status_code = 503
    message = "GitHub is unavailable, try again shortly"
