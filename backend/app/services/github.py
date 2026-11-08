import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime, timezone

import httpx

from app.core.config import Settings, get_settings
from app.core.errors import (
    RateLimitedError,
    RepositoryNotFoundOnGitHub,
    UpstreamUnavailableError,
)

logger = logging.getLogger(__name__)

RETRYABLE_STATUS = {500, 502, 503, 504}


@dataclass(frozen=True)
class GitHubRepository:
    owner: str
    name: str
    full_name: str
    html_url: str
    description: str | None
    primary_language: str | None
    stars_count: int
    forks_count: int
    open_issues_count: int
    watchers_count: int
    github_created_at: datetime | None


def _parse_timestamp(raw: str | None) -> datetime | None:
    if not raw:
        return None
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return None


def _reset_at(response: httpx.Response) -> str | None:
    raw = response.headers.get("x-ratelimit-reset")
    if not raw:
        return None
    try:
        return datetime.fromtimestamp(int(raw), tz=timezone.utc).isoformat()
    except (TypeError, ValueError):
        return None


class GitHubClient:
    """The only code that talks to GitHub. Raises typed errors, never leaks responses."""

    def __init__(
        self,
        settings: Settings | None = None,
        transport: httpx.AsyncBaseTransport | None = None,
    ):
        self.settings = settings or get_settings()
        self._transport = transport

    def _headers(self) -> dict[str, str]:
        headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "repopulse",
        }
        if self.settings.github_token:
            headers["Authorization"] = f"Bearer {self.settings.github_token}"
        return headers

    async def _request(self, path: str) -> httpx.Response:
        url = f"{self.settings.github_api_base}{path}"
        attempts = self.settings.github_max_retries + 1
        last_error: Exception | None = None

        async with httpx.AsyncClient(
            timeout=self.settings.github_timeout_seconds,
            transport=self._transport,
            headers=self._headers(),
        ) as client:
            for attempt in range(attempts):
                try:
                    response = await client.get(url)
                except (httpx.TimeoutException, httpx.TransportError) as exc:
                    last_error = exc
                    logger.warning("GitHub request to %s failed on network", path)
                else:
                    if response.status_code == 404:
                        raise RepositoryNotFoundOnGitHub(
                            "That public repository does not exist on GitHub"
                        )
                    if response.status_code in (403, 429) and self._is_rate_limited(
                        response
                    ):
                        raise RateLimitedError(
                            "GitHub API rate limit reached. Add a GITHUB_TOKEN or "
                            "retry after the reset time.",
                            reset_at=_reset_at(response),
                        )
                    if response.status_code in RETRYABLE_STATUS:
                        last_error = UpstreamUnavailableError(
                            f"GitHub responded with {response.status_code}"
                        )
                        logger.warning(
                            "GitHub request to %s returned %s",
                            path,
                            response.status_code,
                        )
                    elif response.is_success:
                        return response
                    else:
                        raise UpstreamUnavailableError(
                            f"GitHub responded with an unexpected status "
                            f"({response.status_code})"
                        )

                if attempt < attempts - 1:
                    await asyncio.sleep(0.5 * (2**attempt))

        raise UpstreamUnavailableError(
            "GitHub could not be reached after retrying"
        ) from last_error

    @staticmethod
    def _is_rate_limited(response: httpx.Response) -> bool:
        if response.status_code == 429:
            return True
        remaining = response.headers.get("x-ratelimit-remaining")
        if remaining == "0":
            return True
        body = response.text.lower() if response.text else ""
        return "rate limit" in body

    async def fetch_repository(self, owner: str, name: str) -> GitHubRepository:
        response = await self._request(f"/repos/{owner}/{name}")
        try:
            payload = response.json()
        except ValueError as exc:
            raise UpstreamUnavailableError(
                "GitHub returned a response that could not be read"
            ) from exc

        if not isinstance(payload, dict) or "full_name" not in payload:
            raise UpstreamUnavailableError("GitHub returned an unexpected payload")

        owner_login = (payload.get("owner") or {}).get("login") or owner
        return GitHubRepository(
            owner=owner_login,
            name=payload.get("name") or name,
            full_name=payload["full_name"],
            html_url=payload.get("html_url")
            or f"https://github.com/{payload['full_name']}",
            description=payload.get("description"),
            primary_language=payload.get("language"),
            stars_count=int(payload.get("stargazers_count") or 0),
            forks_count=int(payload.get("forks_count") or 0),
            open_issues_count=int(payload.get("open_issues_count") or 0),
            watchers_count=int(payload.get("watchers_count") or 0),
            github_created_at=_parse_timestamp(payload.get("created_at")),
        )

    async def fetch_languages(self, owner: str, name: str) -> dict[str, int]:
        response = await self._request(f"/repos/{owner}/{name}/languages")
        try:
            payload = response.json()
        except ValueError as exc:
            raise UpstreamUnavailableError(
                "GitHub returned a language response that could not be read"
            ) from exc

        if not isinstance(payload, dict):
            raise UpstreamUnavailableError(
                "GitHub returned an unexpected language payload"
            )

        languages: dict[str, int] = {}
        for language, size in payload.items():
            try:
                languages[str(language)] = int(size)
            except (TypeError, ValueError):
                continue
        return languages
