from fastapi import HTTPException
from sqlalchemy.orm import Session
from datetime import datetime

from . import github_service
from ..models.repository import Repository


def get(db: Session, name: str, owner: str) -> Repository | None:
    return (
        db.query(Repository)
        .filter(Repository.name == name)
        .filter(Repository.owner == owner)
        .one_or_none()
    )

async def add(*, db: Session, name: str, owner: str) -> Repository:
    repo = get(db, name, owner)
    if repo is None:
        data = await github_service.get(endpoint=f"/repos/{owner}/{name}")
        if data is None:
            raise HTTPException(status_code=404, detail="Repository not found.")
        repo = Repository(name=name, owner=owner)
        db.add(repo)
        db.commit()

    update(db=db, repo=repo)
    db.refresh(repository)
    return repository


async def update(*, db: Session, repo: Repository) -> None:
    data = await github_service.get(
        endpoint=f"/repos/{repo.owner}/{repo.name}/commits?per_page=1"
    )
    if data is None:
        db.delete(repo)
    elif len(data) > 0:
        date = data[0]["commit"]["author"]["date"]
        repo.last_commit_at = datetime.strptime(date, "%Y-%m-%dT%H:%M:%SZ")
    db.commit()