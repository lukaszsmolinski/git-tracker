import uuid
import pytest


@pytest.mark.anyio
async def test_create_protected(client):
    response = await client.post(
        "/collections",
        json={"name": "collection1", "password": "123"}
    )
    json = response.json()

    assert response.status_code == 201
    assert json["name"] == "collection1"
    assert json["protected"]
    assert "password" not in json


@pytest.mark.parametrize(
    "json", [
        {"name": "collection1"},
        {"name": "collection1", "password": None}
    ]
)
@pytest.mark.anyio
async def test_create_unprotected(client, json):
    response = await client.post(
        "/collections",
        json=json
    )
    json_out = response.json()

    assert response.status_code == 201
    assert json_out["name"] == json["name"]
    assert not json_out["protected"]
    assert "password" not in json_out


@pytest.mark.anyio
async def test_get(client, collection):
    response = await client.get(f"/collections/{collection.id}")
    json = response.json()

    assert response.status_code == 200
    assert json["name"] == collection.name
    assert json["id"] == str(collection.id)
    assert json["protected"] == collection.protected
    assert "password" not in json.keys()


@pytest.mark.anyio
async def test_get_unprotected(client, collection_unprotected):
    response = await client.get(f"/collections/{collection_unprotected.id}")
    json = response.json()

    assert response.status_code == 200
    assert json["name"] == collection_unprotected.name
    assert json["id"] == str(collection_unprotected.id)
    assert json["protected"] == collection_unprotected.protected
    assert "password" not in json.keys()


@pytest.mark.anyio
async def test_get_when_does_not_exist(client):
    response = await client.get(f"/collections/{uuid.uuid4()}")
    json = response.json()

    assert response.status_code == 404


@pytest.mark.anyio
async def test_get_collection_repos(client, collection):
    response = await client.get(f"/collections/{collection.id}/repos")
    json = response.json()

    assert response.status_code == 200
    assert len(json) == len(collection.repositories)


@pytest.mark.anyio
async def get_collection_repos_when_does_not_exist(client):
    response = await client.get(f"/collections/{uuid.uuid4()}")

    assert response.status_code == 404


@pytest.mark.anyio
async def get_collection_repos_when_empty(client, collection):
    response = await client.get(f"/collections/{collection['id']}")
    json = response.json()

    assert response.status_code == 200
    assert len(json) == 0


@pytest.mark.anyio
async def test_add_repository_to_unprotected_collection(
    client, collection_unprotected
):
    response = await client.post(
        f"/collections/{collection_unprotected.id}/repos",
        json={
            "repository_name": "Hello-World", 
            "repository_owner": "octocat",
            "provider": "github"
        }
    )

    assert response.status_code == 200


@pytest.mark.anyio
async def test_add_repository_to_protected_collection(auth_client, collection):
    response = await auth_client.post(
        f"/collections/{collection.id}/repos",
        json={
            "repository_name": "Hello-World", 
            "repository_owner": "octocat",
            "provider": "github"
        }
    )

    assert response.status_code == 200



@pytest.mark.parametrize(
    "headers", [{"Authorization": "Bearer 456"}, None]
)
@pytest.mark.anyio
async def test_add_repository_to_collection_when_unauthorized(
    client, collection, headers
):
    response = await client.post(
        f"/collections/{collection.id}/repos",
        json={
            "repository_name": "Hello-World", 
            "repository_owner": "octocat",
            "provider": "github"
        },
        headers=headers
    )

    assert response.status_code == 401


@pytest.mark.anyio
async def test_remove_repository_from_collection(auth_client, collection_not_empty):
    repo_id = collection_not_empty.repositories[0].id
    response = await auth_client.delete(
        f"/collections/{collection_not_empty.id}/repos/{repo_id}",
    )

    assert response.status_code == 200


@pytest.mark.parametrize(
    "headers", [{"Authorization": "Bearer 456"}, None]
)
@pytest.mark.anyio
async def test_remove_repository_from_collection_when_unauthorized(
    client, collection_not_empty, headers
):
    repo_id = collection_not_empty.repositories[0].id
    response = await client.delete(
        f"/collections/{collection_not_empty.id}/repos/{repo_id}",
        headers=headers
    )

    assert response.status_code == 401


@pytest.mark.anyio
async def test_delete_unprotected(client, collection_unprotected):
    response = await client.delete(f"/collections/{collection_unprotected.id}")

    assert response.status_code == 200


@pytest.mark.anyio
async def test_delete_protected(auth_client, collection):
    response = await auth_client.delete(f"/collections/{collection.id}")

    assert response.status_code == 200


@pytest.mark.parametrize(
    "headers", [{"Authorization": "Bearer 456"}, None]
)
@pytest.mark.anyio
async def test_delete_when_unauthorized(client, collection, headers):
    response = await client.delete(
        f"/collections/{collection.id}",
        headers=headers
    )

    assert response.status_code == 401
