from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from sanatorio_allende.allende_api import Allende


def make_response(status_code: int, payload: Any = None) -> MagicMock:
    response = MagicMock()
    response.status_code = status_code
    response.json.return_value = payload
    return response


class TestAllendeLogin:
    @patch("sanatorio_allende.allende_api.requests.get")
    @patch("sanatorio_allende.allende_api.requests.post")
    def test_login_success(self, mock_post: Any, mock_get: Any) -> None:
        mock_post.return_value = make_response(
            200, {"Access_token": "abc123", "Error": ""}
        )
        mock_get.return_value = make_response(200, {"IdPaciente": 4242})

        allende = Allende()
        auth_header = allende.login("12345678", "secret")

        assert auth_header == "Bearer abc123"
        assert allende.get_auth_header() == "Bearer abc123"
        assert allende.get_user_id() == "4242"

        token_call = mock_post.call_args
        assert token_call[0][0] == "https://miportal.sanatorioallende.com/backend/Token"
        assert token_call[1]["headers"]["Authorization"].startswith("Basic ")
        assert token_call[1]["json"]["NumeroDocumento"] == "MTIzNDU2Nzg="
        assert token_call[1]["json"]["Grant_type"] == "password"
        assert mock_get.call_args[1]["headers"]["authorization"] == "Bearer abc123"

    @patch("sanatorio_allende.allende_api.requests.post")
    def test_login_invalid_credentials(self, mock_post: Any) -> None:
        mock_post.return_value = make_response(
            400, {"Error": "invalid_grant", "Error_description": "Usuario incorrecto"}
        )

        with pytest.raises(Exception, match="Check username or password"):
            Allende().login("12345678", "wrong")

    @patch("sanatorio_allende.allende_api.requests.post")
    def test_login_error_in_successful_response(self, mock_post: Any) -> None:
        mock_post.return_value = make_response(
            200, {"Access_token": None, "Error": "invalid_grant"}
        )

        assert Allende.validate_credentials("12345678", "wrong") is False

    @patch("sanatorio_allende.allende_api.requests.get")
    @patch("sanatorio_allende.allende_api.requests.post")
    def test_login_skipped_when_token_still_valid(
        self, mock_post: Any, mock_get: Any
    ) -> None:
        mock_get.return_value = make_response(200, {})

        allende = Allende("Bearer still-valid")

        assert allende.login("12345678", "secret") == "Bearer still-valid"
        mock_post.assert_not_called()
