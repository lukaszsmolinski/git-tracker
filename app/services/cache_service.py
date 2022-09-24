from datetime import datetime, timedelta
from json import dumps, loads
from sqlalchemy.orm import Session

from app.models.cached_response import CachedResponse


def get(*, db: Session, url: str) -> CachedResponse | None:
    """Returns cached response for given url or None if it wasn't cached."""
    return (
        db.query(CachedResponse)
        .filter(CachedResponse.url == url)
        .one_or_none()
    )


def get_json_dict(*, db: Session, url: str) -> CachedResponse | None:
    """Returns cached response json (as dictionary) or None if the cache
       doesn't exist.
    """
    cache = get(db=db, url=url)
    return (
        loads(cache.json)
        if cache is not None and cache.json is not None
        else None
    )


def update(
    *, db: Session, url: str, json: str | None, etag: str | None
) -> CachedResponse:
    """Updates cache for given url (or creates it if it doesn't exist).

    If the cache for given url already exists, then it's deleted.
    """
    cache = get(db=db, url=url)
    if cache is None or cache.etag != etag:
        if cache is not None:
            db.delete(cache)

        cache = CachedResponse(url=url, json=json, etag=etag)
        db.add(cache)
        db.commit()
