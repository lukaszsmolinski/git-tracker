from datetime import datetime, timezone
from fastapi import HTTPException
from sqlalchemy.orm import Session

from . import provider_service
from app.models.repository import Repository, Provider


def get(
    *, db: Session, name: str, owner: str, provider: Provider
) -> Repository | None:
    """Returns repository with given name, owner and provider or None if it
       is doesn't exist in the database.

    Returned repository may not be up to date, as it only contains data that
    is currently present in the database.
    """
    return (
        db.query(Repository)
        .filter(Repository.name == name)
        .filter(Repository.owner == owner)
        .filter(Repository.provider == provider)
        .one_or_none()
    )


async def add(
    *, db: Session, name: str, owner: str, provider: Provider
) -> Repository:
    """Adds a repository to the database.

    If it doesn't exist, raises HTTPException. If it's already added,
    does nothing.
    """
    await _assert_exists(db=db, name=name, owner=owner, provider=provider)

    repo = get(db=db, name=name, owner=owner, provider=provider)
    if repo is None:
        repo = Repository(name=name, owner=owner, provider=provider)
        db.add(repo)
        db.commit()
        db.refresh(repo)

    return repo


async def update(*, db: Session, repo: Repository) -> None:
    """Updates the repository data.

    If the repository no longer exists, removes it.
    """
    exists = await _exists(
        db=db, name=repo.name, owner=repo.owner, provider=repo.provider
    )
    if not exists:
        db.delete(repo)
        db.commit()
        return

    if Provider.GITHUB == repo.provider:
        await _update_github(db=db, repo=repo)
    if Provider.GITLAB == repo.provider:
        await _update_gitlab(db=db, repo=repo)


async def _update_github(*, db: Session, repo: Repository):
    """Updates GitHub repo data."""
    # update last_commit_at
    endpoint = f"/repos/{repo.owner}/{repo.name}/commits?per_page=1"
    data = await provider_service.get(
        db=db, provider=repo.provider, endpoint=endpoint
    )
    if len(data) > 0:
        date = data[0]["commit"]["author"]["date"]
        repo.last_commit_at = provider_service.parse_date(
            date=date, provider=repo.provider
        )

    # update last_release_at
    endpoint = f"/repos/{repo.owner}/{repo.name}/releases?per_page=1"
    data = await provider_service.get(
        db=db, provider=repo.provider, endpoint=endpoint
    )
    if len(data) > 0:
        date = data[0]["published_at"]
        repo.last_release_at = provider_service.parse_date(
            date=date, provider=repo.provider
        )

    db.commit()


async def _update_gitlab(*, db: Session, repo: Repository) -> None:
    """Updates GitLab repo data."""
    # update last_commit_at
    endpoint = f"/projects/{repo.owner}%2F{repo.name}/repository/commits?per_page=1"
    data = await provider_service.get(
        db=db, provider=repo.provider, endpoint=endpoint
    )
    if len(data) > 0:
        date = data[0]["committed_date"]
        repo.last_commit_at = provider_service.parse_date(
            date=date, provider=repo.provider
        )

    # update last_release_at
    endpoint = f"/projects/{repo.owner}%2F{repo.name}/releases?per_page=1"
    data = await provider_service.get(
        db=db, provider=repo.provider, endpoint=endpoint
    )
    if len(data) > 0:
        date = data[0]["released_at"]
        repo.last_release_at = provider_service.parse_date(
            date=date, provider=repo.provider
        )

    db.commit()


async def _exists(
    *, db: Session, name: str, owner: str, provider: Provider
) -> bool:
    """Checks if the repository exists."""
    if Provider.GITHUB == provider:
        endpoint = f"/repos/{owner}/{name}"
    if Provider.GITLAB == provider:
        endpoint = f"/projects/{owner}%2F{name}"

    data = await provider_service.get(db=db, provider=provider, endpoint=endpoint)
    return data is not None


async def _assert_exists(
    *, db: Session, name: str, owner: str, provider: Provider
) -> None:
    """Raises HTTPException if the repository does not exist."""
    if not await _exists(db=db, name=name, owner=owner, provider=provider):
        raise HTTPException(status_code=404, detail="Repository not found.")
