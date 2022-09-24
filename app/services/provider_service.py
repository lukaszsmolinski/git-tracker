from json import dumps, loads
from fastapi import HTTPException
from httpx import AsyncClient
from sqlalchemy.orm import Session

from app.enums import Provider
from app.config import settings
from app.models.cached_response import CachedResponse
from . import cache_service


async def get(*, db: Session, provider: Provider, endpoint: str) -> dict | None:
    """Performs GET request to given endpoint of GitHub API.

    Returns requested data or None if the data wasn't found.
    """
    url = _get_url(endpoint=endpoint, provider=provider)

    async with _get_client(db=db, provider=provider, url=url) as client:
        return _handle_response(
            db=db, provider=provider, response = await client.get(url), url=url
        )


def _handle_response(
    *, db: Session, provider: Provider, response, url: str
) -> dict | None:
    """Handles received response.

    If request was successful, returns response content and saves it to the
    database. If it wasn't, raises HTTPException with appropriate message
    and code 503.
    """
    # Cache response if it was successful.
    if response.status_code in [200, 404]:
        json = dumps(response.json()) if response.status_code == 200 else None
        etag = None
        if "ETag" in response.headers.keys():
            etag = response.headers["ETag"]
        if "etag" in response.headers.keys():
            etag = response.headers["etag"]
        cache_service.update(db=db, url=url, json=json, etag=etag)

    # Return cached response.
    if response.status_code in [200, 304, 404]:
        return cache_service.get_json_dict(db=db, url=url)

    _handle_error_code(code=response.status_code, provider=provider)


def _get_url(*, endpoint: str, provider: Provider) -> str:
    """Creates an url."""
    if endpoint[0] != "/":
        enpoint = "/" + endpoint

    if Provider.GITHUB == provider:
        return "https://api.github.com" + endpoint
    if Provider.GITLAB == provider:
        return "https://gitlab.com/api/v4" + endpoint


def _get_client(*, db: Session, provider: Provider, url: str) -> AsyncClient:
    """Creates default client for requests.

    Uses auth data if it's present among enviroment variables.
    """
    headers = {}
    auth = None

    cache = cache_service.get(db=db, url=url)
    etag = cache.etag if cache is not None else None
    if etag is not None:
        headers["If-None-Match"] = etag

    if Provider.GITHUB == provider:
        headers["Accept"] = "application/vnd.github.v3+json"
        auth = (
            (settings.github_username, settings.github_token)
            if settings.github_username and settings.github_token
            else None
        )
    if Provider.GITLAB == provider:
        auth = (
            (settings.gitlab_username, settings.gitlab_token)
            if settings.gitlab_username and settings.gitlab_token
            else None
        )

    return AsyncClient(auth=auth, headers=headers)


def _handle_error_code(*, code: int, provider: Provider):
    """"Raises HTTPException depending on provider and status code."""
    msg = "Unknown error occured while connecting to external API."

    if Provider.GITHUB == provider:
        msg = "Unknown error occured while connecting to GitHub API."
        if 401 == code:
            msg = "Bad credentials to GitHub API."
        if 403 == code:
            msg = (
                "Exceeded rate limit or too many unsuccesful authentication "
                "attempts to GitHub API."
            )

    if Provider.GITLAB == provider:
        msg = "Unknown error occured while connecting to GitLab API."
        if 401 == code:
            msg = "Bad credentials to GitLab API."
        if 429 == code:
            msg = "Exceeded rate limit to GitLab API."
        if 403 == code:
            msg = "Too many unsuccesful authentication attempts to GitLab API."

    raise HTTPException(status_code=503, detail=msg)
