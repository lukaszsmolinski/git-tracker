from datetime import datetime, timezone
from fastapi import HTTPException
from sqlalchemy.orm import Session

from . import github_service, gitlab_service
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
    match repo.provider:
        case Provider.GITHUB:
            await _update_github(db=db, repo=repo)
        case Provider.GITLAB:
            await _update_gitlab(db=db, repo=repo)


async def _update_github(*, db: Session, repo: Repository) -> None:
    """Updates GitHub repository or removes it if it no longer exists."""
    data = await github_service.get(
        db=db,
        endpoint=f"/repos/{repo.owner}/{repo.name}/commits?per_page=1"
    )
    if data is None:
        db.delete(repo)
    elif len(data) > 0:
        date = data[0]["commit"]["author"]["date"]
        repo.last_commit_at = datetime.strptime(date, "%Y-%m-%dT%H:%M:%SZ")
    db.commit()


async def _update_gitlab(*, db: Session, repo: Repository) -> None:
    """Updates GitLab repository or removes it if it no longer exists."""
    data = await gitlab_service.get(
        db=db,
        endpoint=f"/projects/{repo.owner}%2F{repo.name}/repository/commits?per_page=1"
    )
    if data is None:
        db.delete(repo)
    elif len(data) > 0:
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
    data = None
    match provider:
        case Provider.GITHUB:
            data = await github_service.get(
                db=db, endpoint=f"/repos/{owner}/{name}"
            )
        case Provider.GITLAB:
            data = await gitlab_service.get(
                db=db, endpoint=f"/projects/{owner}%2F{name}"
            )
    if data is None:
        raise HTTPException(status_code=404, detail="Repository not found.")
