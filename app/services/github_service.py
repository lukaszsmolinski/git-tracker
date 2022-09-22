from json import dumps, loads
from aiohttp import BasicAuth, ClientSession
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.config import settings
from app.models.cached_response import CachedResponse
from . import cache_service

BASE_URL = "https://api.github.com"


async def get(*, db: Session, endpoint: str) -> dict | None:
    """Performs GET request to given endpoint of GitHub API.

    Returns requested data or None if the data wasn't found.
    """
    url = BASE_URL + endpoint

    cache = cache_service.get(db=db, url=url)
    etag = cache.etag if cache is not None else None

    async with _default_client(etag=etag) as session:
        async with session.get(url) as response:
            return await _handle_response(db=db, response=response, url=url)


def _default_client(etag: str = None):
    """Creates default client session for requests to GitHub API.

    If GITHUB_USERNAME and GITHUB_TOKEN environment variables are set,
    then creates authenticated session, which has greater hourly rate limit.
    """
    headers = {
        "Accept": "application/vnd.github.v3+json"
    }
    if etag is not None:
        headers["If-None-Match"] = etag
    auth = (
        BasicAuth(settings.github_username, settings.github_token)
        if settings.github_username and settings.github_token
        else None
    )
    return ClientSession(auth=auth, headers=headers)


async def _handle_response(*, db: Session, response, url: str) -> dict | None:
    """Handles received response.

    If request was successful, returns response content and saves it to the
    database. If it wasn't, raises HTTPException with appropriate message
    and code 503.
    """
    if response.status in [200, 404]:
        json = dumps(await response.json()) if response.status == 200 else None
        etag = (
            response.headers["ETag"]
            if "ETag" in response.headers.keys()
            else None
        )
        cache_service.update(
            db=db, url=url, json=json, etag=etag
        )
    if response.status in [200, 304, 404]:
        cache = cache_service.get(db=db, url=url)
        json_dict = loads(cache.json) if cache.json is not None else None
        return json_dict

    match response.status:
        case 401:
            detail = "Bad credentials to GitHub API."
        case 403:
            limit_reached = response.headers['X-RateLimit-Remaining'] == '0'
            detail = (
                "Exceeded rate limit to GitHub API."
                if limit_reached
                else "Too many unsuccesful authentication attempts to GitHub API."
            )
        case _:
            message = "Unknown error occured while connecting to GitHub API."
    raise HTTPException(status_code=503, detail=detail)
