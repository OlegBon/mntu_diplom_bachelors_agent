import pytest


@pytest.mark.api
@pytest.mark.integration
@pytest.mark.parametrize(
    ("method", "path"),
    [
        ("get", "/diamonds/"),
        ("get", "/diamonds/DR-01000"),
        ("post", "/diamonds/"),
        ("put", "/diamonds/DR-01000"),
        ("delete", "/diamonds/DR-01000"),
    ],
)
def test_legacy_diamond_routes_are_not_exposed(client, method: str, path: str) -> None:
    request = getattr(client, method)
    response = request(path, json={}) if method in {"post", "put"} else request(path)

    assert response.status_code == 404
