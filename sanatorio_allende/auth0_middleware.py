import json

import requests
from django.conf import settings
from django.contrib.auth import get_user_model, login
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin
from jose import JWTError, jwt

User = get_user_model()


class Auth0Middleware(MiddlewareMixin):
    """
    Middleware to handle Auth0 JWT token validation
    """

    def __init__(self, get_response):
        super().__init__(get_response)
        self.auth0_domain = getattr(settings, "AUTH0_DOMAIN", None)
        self.auth0_audience = getattr(settings, "AUTH0_AUDIENCE", None)
        self.auth0_issuer = getattr(settings, "AUTH0_ISSUER", None)
        self.auth0_client_id = getattr(settings, "AUTH0_MANAGEMENT_CLIENT_ID", None)
        self.auth0_client_secret = getattr(
            settings, "AUTH0_MANAGEMENT_CLIENT_SECRET", None
        )

        if not all(
            [
                self.auth0_domain,
                self.auth0_audience,
                self.auth0_issuer,
                self.auth0_client_id,
                self.auth0_client_secret,
            ]
        ):
            raise ValueError(
                "AUTH0_DOMAIN, AUTH0_AUDIENCE, AUTH0_ISSUER, AUTH0_CLIENT_ID, and AUTH0_CLIENT_SECRET must be set in Django settings"
            )

    def process_request(self, request):
        """
        Process the request and validate the Auth0 JWT token
        """
        # Skip authentication for certain paths (optional)
        if self._should_skip_auth(request.path):
            return None
        # Get the Authorization header
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return JsonResponse(
                {"error": "Authorization header is required"}, status=401
            )

        # Extract the token
        try:
            token = auth_header.split(" ")[1]  # Bearer <token>
        except IndexError:
            return JsonResponse(
                {"error": "Invalid authorization header format"}, status=401
            )

        # Validate the token
        try:
            payload = self._validate_token(token)
            user = self._get_or_create_user(payload)
            login(request, user)
            return None
        except Exception as e:
            return JsonResponse(
                {"error": f"Token validation failed: {str(e)}"}, status=401
            )

    def _should_skip_auth(self, path):
        """
        Define paths that don't require authentication
        """
        skip_paths = [
            "/admin/",
            "/login",
            "/auth/callback/",
        ]
        return any(path.startswith(skip_path) for skip_path in skip_paths)

    def _validate_token(self, token):
        """
        Validate the JWT token using Auth0's public key
        """
        try:
            # Get Auth0's public key
            jwks_url = f"https://{self.auth0_domain}/.well-known/jwks.json"
            jwks = requests.get(jwks_url).json()

            # Decode the token header to get the key ID
            unverified_header = jwt.get_unverified_header(token)
            rsa_key = {}

            for key in jwks["keys"]:
                if key["kid"] == unverified_header["kid"]:
                    rsa_key = {
                        "kty": key["kty"],
                        "kid": key["kid"],
                        "use": key["use"],
                        "n": key["n"],
                        "e": key["e"],
                    }
                    break

            if not rsa_key:
                raise Exception("Unable to find appropriate key")

            payload = jwt.decode(
                token,
                rsa_key,
                algorithms=["RS256"],
                audience=self.auth0_audience,
                issuer=self.auth0_issuer,
            )

            return payload

        except JWTError as e:
            if "expired" in str(e).lower():
                raise Exception("Token has expired")
            else:
                raise Exception(f"Invalid token: {str(e)}")
        except Exception as e:
            raise Exception(f"Token validation error: {str(e)}")

    def _get_or_create_user(self, payload):
        """
        Get or create a Django user based on Auth0 user info
        """
        auth0_user_id = payload.get("sub")

        try:
            user = User.objects.get(username=auth0_user_id)
        except User.DoesNotExist:
            user = self._create_user_from_auth0(auth0_user_id)

        return user

    def _get_auth0_user_data(self, user_id):
        """
        Fetch user data from Auth0 Management API
        """
        # Get management API token
        management_token = self._get_management_token()

        # Fetch user data from Auth0
        headers = {"Authorization": f"Bearer {management_token}"}
        url = f"https://{self.auth0_domain}/api/v2/users/{user_id}"
        response = requests.get(url, headers=headers)

        response.raise_for_status()
        return response.json()

    def _get_management_token(self):
        """
        Get Auth0 Management API token
        """
        token_url = f"https://{self.auth0_domain}/oauth/token"
        payload = {
            "client_id": self.auth0_client_id,
            "client_secret": self.auth0_client_secret,
            "audience": self.auth0_audience,
            "grant_type": "client_credentials",
            "scope": "read:users",
        }

        response = requests.post(token_url, json=payload)
        response.raise_for_status()
        return response.json()["access_token"]

    def _create_user_from_auth0(self, auth0_user_id):
        """
        Create a new Django user with Auth0 data
        """
        # Try to get full user data from Auth0
        auth0_user_data = self._get_auth0_user_data(auth0_user_id)
        email = auth0_user_data.get("email")
        name = auth0_user_data.get("name")
        given_name = auth0_user_data.get("given_name", "")
        family_name = auth0_user_data.get("family_name", "")
        nickname = auth0_user_data.get("nickname", "")

        # Use given_name/family_name if available, otherwise split name
        if given_name and family_name:
            first_name = given_name
            last_name = family_name
        elif name:
            name_parts = name.split(" ", 1)
            first_name = name_parts[0]
            last_name = name_parts[1] if len(name_parts) > 1 else ""
        else:
            first_name = nickname or ""
            last_name = ""

        user = User.objects.create_user(
            username=auth0_user_id,
            email=email,
            first_name=first_name,
            last_name=last_name,
            is_active=True,
        )

        return user
