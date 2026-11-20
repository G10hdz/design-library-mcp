"""The gallery only listens on 127.0.0.1, but any page open in the user's browser can still
send it requests: a cross-site form POST, or a DNS-rebinding page that resolves its own
hostname to 127.0.0.1. Writes must come from the gallery itself, and the Host must be ours."""

import pytest
from fastapi.testclient import TestClient

from designlib.core.search import get_entry
from designlib.web.app import create_app

GALLERY = "http://127.0.0.1:8000"


@pytest.fixture
def client():
    return TestClient(create_app(), base_url=GALLERY)


@pytest.mark.parametrize("origin", ["https://evil.example", "null", "http://127.0.0.1:9999"])
def test_cross_origin_write_is_rejected(client, sample_entries, origin):
    response = client.post("/d/pricing-table-aaaaaa/delete", headers={"Origin": origin})
    assert response.status_code == 403
    assert get_entry("pricing-table-aaaaaa") is not None


def test_cross_site_fetch_metadata_write_is_rejected(client, sample_entries):
    response = client.post("/d/pricing-table-aaaaaa/delete", headers={"Sec-Fetch-Site": "cross-site"})
    assert response.status_code == 403
    assert get_entry("pricing-table-aaaaaa") is not None


def test_same_origin_write_is_allowed(client, sample_entries):
    response = client.post(
        "/d/pricing-table-aaaaaa/delete",
        headers={"Origin": GALLERY, "Sec-Fetch-Site": "same-origin"},
        follow_redirects=False,
    )
    assert response.status_code == 303
    assert get_entry("pricing-table-aaaaaa") is None


@pytest.mark.parametrize("host", ["evil.example", "evil.example:8000"])
def test_foreign_host_is_rejected(client, sample_entries, host):
    response = client.get("/", headers={"Host": host})
    assert response.status_code == 400


def test_localhost_host_is_allowed(client):
    assert client.get("/", headers={"Host": "localhost:8000"}).status_code == 200
