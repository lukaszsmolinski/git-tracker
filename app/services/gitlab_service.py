from json import dumps, loads
from aiohttp import ClientSession
from fastapi import HTTPException
from sqlalchemy.orm import Session

from . import cache_service

BASE_URL = "https://gitlab.com/api/v4"


async def get(*, db: Session, endpoint: str) -> dict | None:
    """Performs GET request to given endpoint of GitLab API.

    Returns requested data or None if the data wasn't found.
    """
    url = BASE_URL + endpoint

    cache = cache_service.get(db=db, url=url)
    etag = cache.etag if cache is not None else None

    async with _default_client(etag=etag) as session:
        async with session.get(url) as response:
            return await _handle_response(db=db, response=response, url=url)


def _default_client(etag: str = None):
    """Creates default client session for requests to GitLab API."""
    headers = {}
    if etag is not None:
        headers["If-None-Match"] = etag
    return ClientSession(headers=headers)


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
            detail = "Bad credentials to GitLab API."
        case 429:
            detail = "Exceeded rate limit to GitLab API."
        case 403:
            detail = "Too many unsuccesful authentication attempts to GitLab API."
        case _:
            detail = "Unknown error occured while connecting to GitLab API."
    raise HTTPException(status_code=503, detail=detail)
