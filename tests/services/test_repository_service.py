import pytest
from fastapi import HTTPException

from app.enums import Provider
from app.models.repository import Repository
from app.services import repository_service


EXISTING_REPOS_DATA = [
    {
        "name": "Hello-World",
        "owner": "octocat",
        "provider": Provider.GITHUB
    },
    {
        "name": "gitlab",
        "owner": "gitlab-org",
        "provider": Provider.GITLAB
    }
]

NONEXISTENT_REPOS_DATA = [
    {
        "name": "does-not-exist",
        "owner": "asdfdsasddsfafdsa",
        "provider": Provider.GITHUB
    },
    {
        "name": "does-not-exist",
        "owner": "sadkdsaklsdj",
        "provider": Provider.GITLAB
    }
]


@pytest.mark.parametrize("data", EXISTING_REPOS_DATA)
@pytest.mark.anyio
async def test_get(db, data):
    await repository_service.add(db=db, **data)

    repo = repository_service.get(db=db, **data)

    assert data.items() <= repo.__dict__.items()


@pytest.mark.parametrize("data", EXISTING_REPOS_DATA + NONEXISTENT_REPOS_DATA)
def test_get_when_was_not_added(db, data):
    repo = repository_service.get(db=db, **data)

    assert repo is None


@pytest.mark.parametrize("data", EXISTING_REPOS_DATA)
@pytest.mark.anyio
async def test_add(db, data):
    repo = await repository_service.add(db=db, **data)

    assert data.items() <= repo.__dict__.items()
    assert repo.last_commit_at is None


@pytest.mark.parametrize("data", NONEXISTENT_REPOS_DATA)
@pytest.mark.anyio
async def test_add_when_repo_does_not_exist(db, data):
    with pytest.raises(HTTPException) as excinfo:
        await repository_service.add(db=db, **data)

    assert excinfo.value.status_code == 404
    assert repository_service.get(db=db, **data) is None


@pytest.mark.parametrize("data", EXISTING_REPOS_DATA)
@pytest.mark.anyio
async def test_add_twice(db, data):
    rows_before = db.query(Repository).count()
    await repository_service.add(db=db, **data)
    await repository_service.add(db=db, **data)
    rows_after = db.query(Repository).count()

    assert rows_after - rows_before == 1


@pytest.mark.parametrize(
    "data, has_release",
    [
        [{
            "name": "Hello-World",
            "owner": "octocat",
            "provider": Provider.GITHUB
        }, False],
        [{
            "name": "linguist",
            "owner": "github",
            "provider": Provider.GITHUB
        }, True],
        [{
            "name": "gitlab",
            "owner": "gitlab-org",
            "provider": Provider.GITLAB
        }, True]
    ]
)
@pytest.mark.anyio
async def test_update(db, data, has_release):
    repo = await repository_service.add(db=db, **data)

    await repository_service.update(db=db, repo=repo)

    repo = repository_service.get(db=db, **data)
    assert repo.last_commit_at is not None
    if has_release:
        assert repo.last_release_at is not None
    else:
        assert repo.last_release_at is None


@pytest.mark.parametrize("data", NONEXISTENT_REPOS_DATA)
@pytest.mark.anyio
async def test_update_when_repo_no_longer_exists(db, data):
    # Repo doesn't exist so we must add it artificially to the database.
    repo = Repository(**data)
    db.add(repo)
    db.commit()
    db.refresh(repo)

    await repository_service.update(db=db, repo=repo)

    assert repository_service.get(db=db, **data) is None


@pytest.mark.parametrize("data", EXISTING_REPOS_DATA)
@pytest.mark.anyio
async def test_exists_and_assert_exists_when_repo_exists(db, data):
    await repository_service._assert_exists(db=db, **data)
    assert await repository_service._exists(db=db, **data)


@pytest.mark.parametrize("data", NONEXISTENT_REPOS_DATA)
@pytest.mark.anyio
async def test_assert_exists_when_repo_does_not_exist(db, data):
    with pytest.raises(HTTPException) as excinfo:
        await repository_service._assert_exists(db=db, **data)

    assert excinfo.value.status_code == 404
    assert not await repository_service._exists(db=db, **data)
