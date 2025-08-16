from django.conf import settings


def pytest_configure() -> None:
    """Globally remove the auth0 middleware for all tests"""
    settings.MIDDLEWARE.remove("sanatorio_allende.auth0_middleware.Auth0Middleware")
