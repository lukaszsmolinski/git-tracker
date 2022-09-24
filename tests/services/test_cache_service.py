from app.models.cached_response import CachedResponse
from app.services import cache_service


def test_get_when_cache_exists1(db):
    url = "https://www.example.com"
    json = '{"value": "test"}'
    etag = "1"
    db.add(CachedResponse(url=url, json=json, etag=etag))
    db.commit()

    cache = cache_service.get(db=db, url=url)

    assert cache.url == url
    assert cache.json == json
    assert cache.etag == etag


def test_get_when_cache_exists2(db):
    url = "https://www.example.com"
    json = '{"value": "test"}'
    etag = "1"
    cache_service.update(db=db, url=url, json=json, etag=etag)

    cache = cache_service.get(db=db, url=url)

    assert cache.url == url
    assert cache.json == json
    assert cache.etag == etag


def test_get_when_cache_does_not_exist(db):
    url = "https://www.example.com"
    cache = cache_service.get(db=db, url=url)

    assert cache is None


def test_get_json_dict_when_cache_exists(db):
    url = "https://www.example.com"
    json = '{"value": "test"}'
    etag = "1"
    cache_service.update(db=db, url=url, json=json, etag=etag)

    json_dict = cache_service.get_json_dict(db=db, url=url)

    assert json_dict == {"value": "test"}


def test_get_json_dict_when_cache_exists_but_json_is_none(db):
    url = "https://www.example.com"
    etag = "1"
    cache_service.update(db=db, url=url, json=None, etag=etag)

    json_dict = cache_service.get_json_dict(db=db, url=url)

    assert json_dict is None


def test_get_json_dict_when_cache_does_not_exist(db):
    url = "https://www.example.com"
    json_dict = cache_service.get_json_dict(db=db, url=url)

    assert json_dict is None


def test_update_when_cache_does_not_exist(db):
    url = "https://www.example.com"
    json = '{"value": "test"}'
    etag = "1"
    cnt = db.query(CachedResponse).count()

    cache_service.update(db=db, url=url, json=json, etag=etag)

    cache = cache_service.get(db=db, url=url)
    assert db.query(CachedResponse).count() == cnt + 1
    assert cache.url == url
    assert cache.json == json
    assert cache.etag == etag


def test_update_when_cache_exists(db):
    cnt = db.query(CachedResponse).count()
    url = "https://www.example.com"
    json1 = '{"value": "test1"}'
    etag1 = "1"
    cache_service.update(db=db, url=url, json=json1, etag=etag1)

    json2 = '{"value": "test2"}'
    etag2 = "2"
    cache_service.update(db=db, url=url, json=json2, etag=etag2)

    cache = cache_service.get(db=db, url=url)
    assert db.query(CachedResponse).count() == cnt + 1
    assert cache.url == url
    assert cache.json != json1
    assert cache.json == json2
    assert cache.etag != etag1
    assert cache.etag == etag2
