from pydantic import BaseModel


class ErrorResponse(BaseModel):
    """The single error shape every failing endpoint returns."""

    detail: str
    code: str
