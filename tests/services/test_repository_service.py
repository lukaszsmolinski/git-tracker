import pytest
from fastapi import HTTPException

from app.models.repository import Provider, Repository
from app.services import repository_service


@pytest.mark.parametrize(
    "data",
    [
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
)
@pytest.mark.asyncio
async def test_get(db, data):
    await repository_service.add(db=db, **data)

    repo = repository_service.get(db=db, **data)

    assert data.items() <= repo.__dict__.items()


@pytest.mark.parametrize(
    "data",
    [
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
)
def test_get_when_does_not_exist(db, data):
    repo = repository_service.get(db=db, **data)

    assert repo is None


@pytest.mark.parametrize(
    "data",
    [
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
)
@pytest.mark.asyncio
async def test_add(db, data):
    repo = await repository_service.add(db=db, **data)

    assert data.items() <= repo.__dict__.items()
    assert repo.last_commit_at is None


@pytest.mark.parametrize(
    "data",
    [
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
)
@pytest.mark.asyncio
async def test_add_when_repo_does_not_exist(db, data):
    with pytest.raises(HTTPException) as excinfo:
        await repository_service.add(db=db, **data)

    assert excinfo.value.status_code == 404
    assert repository_service.get(db=db, **data) is None


@pytest.mark.parametrize(
    "data",
    [
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
)
@pytest.mark.asyncio
async def test_add_twice(db, data):
    rows_before = db.query(Repository).count()
    await repository_service.add(db=db, **data)
    await repository_service.add(db=db, **data)
    rows_after = db.query(Repository).count()

    assert rows_after - rows_before == 1


@pytest.mark.parametrize(
    "data, function_mock",
    [
        [
            {
                "name": "Hello-World",
                "owner": "octocat",
                "provider": Provider.GITHUB
            },
            "app.services.repository_service._update_github"
        ],
        [
            {
                "name": "gitlab",
                "owner": "gitlab-org",
                "provider": Provider.GITLAB
            },
            "app.services.repository_service._update_gitlab"
        ]
    ]
)
@pytest.mark.asyncio
async def test_update(db, mocker, data, function_mock):
    mocked_function = mocker.patch(function_mock)
    repo = await repository_service.add(db=db, **data)
    await repository_service.update(db=db, repo=repo)
    mocked_function.assert_called_once()


@pytest.mark.asyncio
async def test_update_github(db):
    data = {
        "name": "Hello-World",
        "owner": "octocat",
        "provider": Provider.GITHUB
    }
    repo = await repository_service.add(db=db, **data)

    await repository_service._update_github(db=db, repo=repo)
    repo = repository_service.get(db=db, **data)

    assert repo is not None
    assert repo.last_commit_at is not None


@pytest.mark.asyncio
async def test_update_github_when_repo_no_longer_exists(db):
    data = {
        "name": "no-longer-exists",
        "owner": "dsdfsdfsd",
        "provider": Provider.GITHUB
    }
    repo = Repository(**data)
    db.add(repo)
    db.commit()
    db.refresh(repo)

    await repository_service._update_github(db=db, repo=repo)

    assert repository_service.get(db=db, **data) is None


@pytest.mark.asyncio
async def test_update_gitlab(db):
    data = {
        "name": "gitlab",
        "owner": "gitlab-org",
        "provider": Provider.GITLAB
    }
    repo = await repository_service.add(db=db, **data)

    await repository_service._update_gitlab(db=db, repo=repo)
    repo = repository_service.get(db=db, **data)

    assert repo is not None
    assert repo.last_commit_at is not None


@pytest.mark.asyncio
async def test_update_gitlab_when_repo_no_longer_exists(db):
    data = {
        "name": "no-longer-exists",
        "owner": "dsdfsdfsd",
        "provider": Provider.GITLAB
    }
    repo = Repository(**data)
    db.add(repo)
    db.commit()
    db.refresh(repo)

    await repository_service._update_gitlab(db=db, repo=repo)

    assert repository_service.get(db=db, **data) is None


@pytest.mark.parametrize(
    "data",
    [
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
)
@pytest.mark.asyncio
async def test_assert_exists_when_repo_exists(db, data):
    await repository_service._assert_exists(**data)


@pytest.mark.parametrize(
    "data",
    [
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
)
@pytest.mark.asyncio
async def test_assert_exists_when_repo_does_not_exist(db, data):
    with pytest.raises(HTTPException) as excinfo:
        await repository_service._assert_exists(**data)

    assert excinfo.value.status_code == 404
