import pytest

from dakara_server import token_auth


@pytest.mark.asyncio
class TestTokenAuthMiddleware:
    async def test_auth_header(self, mocker):
        """Test to authenticate through WebSocket with a token in the headers."""
        mocked_inner = mocker.AsyncMock()
        mocked_get_user = mocker.patch("dakara_server.token_auth.get_user")
        mocked_get_user.return_value = "my user"
        mocked_close_old_connections = mocker.patch(
            "dakara_server.token_auth.close_old_connections"
        )

        scope = {"headers": {b"authorization": b"Token abcd1234"}}
        middleware = token_auth.TokenAuthMiddleware(mocked_inner)

        await middleware(scope, None, None)

        assert scope["user"] == "my user"

        mocked_inner.assert_called_with(scope, None, None)
        mocked_get_user.assert_called_with("abcd1234")
        mocked_close_old_connections.assert_called_with()

    async def test_auth_query_string(self, mocker):
        """Test to authenticate through WebSocket with a token in the query string."""
        mocked_inner = mocker.AsyncMock()
        mocked_get_user = mocker.patch("dakara_server.token_auth.get_user")
        mocked_get_user.return_value = "my user"
        mocked_close_old_connections = mocker.patch(
            "dakara_server.token_auth.close_old_connections"
        )

        scope = {"query_string": b"token=abcd1234"}
        middleware = token_auth.TokenAuthMiddleware(mocked_inner)

        await middleware(scope, None, None)

        assert scope["user"] == "my user"

        mocked_inner.assert_called_with(scope, None, None)
        mocked_get_user.assert_called_with("abcd1234")
        mocked_close_old_connections.assert_called_with()

    async def test_auth_nothing(self, mocker):
        """Test to authenticate through WebSocket with nothing."""
        mocked_inner = mocker.AsyncMock()

        scope = {}
        middleware = token_auth.TokenAuthMiddleware(mocked_inner)

        await middleware(scope, None, None)

        assert "user" not in scope

        mocked_inner.assert_called_with(scope, None, None)
