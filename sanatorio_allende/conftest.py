import sentry_sdk
from django.conf import settings


def pytest_configure() -> None:
    """Globally remove the auth0 middleware for all tests"""
    settings.MIDDLEWARE.remove("sanatorio_allende.auth0_middleware.Auth0Middleware")
    # The settings start Sentry with the real DSN. Tests must not report to it: a
    # cron check-in sent from a test run would count as the scheduled job running.
    sentry_sdk.init(dsn="")
