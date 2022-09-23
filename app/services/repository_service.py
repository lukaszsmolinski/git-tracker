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
    """Updates repository data.

    If the repository no longer exists, removes it.
    """
    if Provider.GITHUB == repo.provider:
        endpoint = f"/repos/{repo.owner}/{repo.name}/commits?per_page=1"
    elif Provider.GITLAB == repo.provider:
        endpoint = f"/projects/{repo.owner}%2F{repo.name}/repository/commits?per_page=1"

    data = await provider_service.get(
        db=db, provider=repo.provider, endpoint=endpoint
    )
    if data is None:
        db.delete(repo)
    elif len(data) > 0:
        if Provider.GITHUB == repo.provider:
            date = data[0]["commit"]["author"]["date"]
            repo.last_commit_at = datetime.strptime(date, "%Y-%m-%dT%H:%M:%SZ")
        elif Provider.GITLAB == repo.provider:
            date = data[0]["committed_date"]
            repo.last_commit_at = (
                datetime.fromisoformat(date).astimezone(timezone.utc)
            )
    db.commit()


async def _assert_exists(
    *, db: Session, name: str, owner: str, provider: Provider
) -> None:
    """Checks if repository with given name, owner and provider exists.

    If it doesn't raises HTTPException.
    """
    if Provider.GITHUB == provider:
        endpoint = f"/repos/{owner}/{name}"
    elif Provider.GITLAB == provider:
        endpoint = f"/projects/{owner}%2F{name}"

    data = await provider_service.get(db=db, provider=provider, endpoint=endpoint)
    if data is None:
        raise HTTPException(status_code=404, detail="Repository not found.")
