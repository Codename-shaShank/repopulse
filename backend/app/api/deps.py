from app.services.github import GitHubClient


def get_github_client() -> GitHubClient:
    """Overridden in tests with a mocked transport."""
    return GitHubClient()
