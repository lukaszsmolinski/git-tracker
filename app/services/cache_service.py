from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.models.cached_response import CachedResponse


def get(*, db: Session, url: str) -> CachedResponse | None:
    """Returns cached response for given url or None if it wasn't cached."""
    return (
        db.query(CachedResponse)
        .filter(CachedResponse.url == url)
        .one_or_none()
    )


def is_cache_valid(
    *, db: Session, cache: CachedResponse | None, seconds: int
) -> bool:
    """Checks if cache was created less than given number of seconds ago."""
    return (
        cache is not None and
        datetime.utcnow() - timedelta(seconds=seconds) <= cache.created_at
    )


def update(
    *, db: Session, url: str, json: str | None, etag: str
) -> CachedResponse:
    """Updates cache for given url with json and etag.

    If the cache for given url already exists, then it's deleted.
    """
    cache = get(db=db, url=url)
    if cache is None or cache.etag != etag:
        if cache is not None:
            db.delete(cache)

        cache = CachedResponse(url=url, json=json, etag=etag)
        db.add(cache)
        db.commit()
