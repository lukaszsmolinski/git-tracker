from fastapi import HTTPException
import pytest

from app.enums import Provider
from app.services import provider_service, cache_service


@pytest.mark.parametrize(
    "provider, endpoint", [
        [Provider.GITHUB, "/repos/octocat/Hello-World"], 
        [Provider.GITLAB, "/projects/gitlab-org%2Fgitlab"]
    ]
)
@pytest.mark.anyio
async def test_get_200(db, provider, endpoint):
    data = await provider_service.get(db=db, provider=provider, endpoint=endpoint)

    assert data is not None
    assert len(data) > 0
    assert "id" in data.keys()
    assert "name" in data.keys()

    url = provider_service._get_url(provider=provider, endpoint=endpoint)
    cache = cache_service.get(db=db, url=url)
    json = cache_service.get_json_dict(db=db, url=url)
    assert cache is not None
    assert cache.json is not None
    assert cache.etag is not None
    assert json == data


@pytest.mark.parametrize(
    "provider, endpoint", [
        [Provider.GITHUB, "/repos/octocat/does-not-exist"], 
        [Provider.GITLAB, "/projects/gitlab-org%2Fdoes-not-exist"]
    ]
)
@pytest.mark.anyio
async def test_get_404(db, provider, endpoint):
    data = await provider_service.get(db=db, provider=provider, endpoint=endpoint)

    assert data is None

    url = provider_service._get_url(provider=provider, endpoint=endpoint)
    cache = cache_service.get(db=db, url=url)
    json = cache_service.get_json_dict(db=db, url=url)
    assert cache is not None
    assert cache.json is None
    assert cache.etag is None
    assert json is None


@pytest.mark.parametrize(
    "provider, endpoint", [
        [Provider.GITHUB, "/repos/octocat/Hello-World"], 
        [Provider.GITLAB, "/projects/gitlab-org%2Fgitlab"]
    ]
)
@pytest.mark.anyio
async def test_get_304_after_200(db, provider, endpoint):
    # now we get 200
    await provider_service.get(db=db, provider=provider, endpoint=endpoint)
    # and now we should get 304
    data = await provider_service.get(db=db, provider=provider, endpoint=endpoint)

    assert data is not None
    assert len(data) > 0
    assert "id" in data.keys()
    assert "name" in data.keys()

    url = provider_service._get_url(provider=provider, endpoint=endpoint)
    cache = cache_service.get(db=db, url=url)
    json = cache_service.get_json_dict(db=db, url=url)
    assert cache is not None
    assert cache.json is not None
    assert cache.etag is not None
    assert json == data


@pytest.mark.parametrize(
    "provider, endpoint, expected", [
        [
            Provider.GITHUB, 
            "/repos/octocat/Hello-World", 
            "https://api.github.com/repos/octocat/Hello-World"
        ], 
        [
            Provider.GITHUB, 
            "repos/octocat/Hello-World", 
            "https://api.github.com/repos/octocat/Hello-World"
        ], 
        [
            Provider.GITLAB, 
            "/projects/gitlab-org%2Fgitlab", 
            "https://gitlab.com/api/v4/projects/gitlab-org%2Fgitlab"
        ], 
        [
            Provider.GITLAB, 
            "projects/gitlab-org%2Fgitlab", 
            "https://gitlab.com/api/v4/projects/gitlab-org%2Fgitlab"
        ]
    ]
)
def test_get_url(provider, endpoint, expected):
    url = provider_service._get_url(endpoint=endpoint, provider=provider)
    assert url == expected


def test_get_client_github(db):
    provider = Provider.GITHUB
    url = "https://api.github.com/repos/octocat/Hello-World"

    client = provider_service._get_client(db=db, provider=provider, url=url)

    keys = [k.lower() for k in client.headers.keys()]
    assert "accept" in keys
    assert "if-none-match" not in keys


def test_get_client_gitlab(db):
    provider = Provider.GITLAB
    url = "https://gitlab.com/api/v4/projects/gitlab-org%2Fgitlab"

    client = provider_service._get_client(db=db, provider=provider, url=url)

    keys = [k.lower() for k in client.headers.keys()]
    assert "if-none-match" not in keys


@pytest.mark.parametrize(
    "provider, endpoint", [
        [
            Provider.GITHUB, 
            "/repos/octocat/Hello-World"
        ],
        [
            Provider.GITLAB, 
            "/projects/gitlab-org%2Fgitlab"
        ]
    ]
)
@pytest.mark.anyio
async def test_get_client_github_when_cache_exists(db, provider, endpoint):
    url = provider_service._get_url(endpoint=endpoint, provider=provider)
    await provider_service.get(
        db=db, provider=provider, endpoint=endpoint
    )

    client = provider_service._get_client(db=db, provider=provider, url=url)

    keys = [k.lower() for k in client.headers.keys()]
    assert "if-none-match" in keys


@pytest.mark.parametrize(
    "code", [401, 403, 404, 429, 500]
)
@pytest.mark.parametrize(
    "provider", Provider
)
def test_handle_error_code(code, provider):
    with pytest.raises(HTTPException) as excinfo:
        provider_service._handle_error_code(code=code, provider=provider)

    assert excinfo.value.status_code == 503
    assert excinfo.value.detail is not None
    assert len(excinfo.value.detail) > 5
