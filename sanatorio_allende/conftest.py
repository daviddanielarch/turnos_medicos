from django.conf import settings


def pytest_configure():
    """Globally remove the your_middleware_to_remove for all tests"""
    settings.MIDDLEWARE.remove("sanatorio_allende.auth0_middleware.Auth0Middleware")
