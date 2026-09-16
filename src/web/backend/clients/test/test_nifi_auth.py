from unittest.mock import Mock

from backend.clients.nifi_auth import NifiAuth


def test_token_is_cached():
    session = Mock()

    response = Mock()
    response.status_code = 200
    response.ok = True
    response.text = "fake-token"

    session.post.return_value = response

    auth = NifiAuth(
        base_url="https://localhost:8443/nifi-api",
        login_payload={
            "username": "admin",
            "password": "password",
        },
        session=session,
        verify=False,
        timeout=10,
    )

    token1 = auth.get_access_token()
    token2 = auth.get_access_token()

    assert token1 == "fake-token"
    assert token2 == "fake-token"

    # Chỉ login đúng một lần
    assert session.post.call_count == 1