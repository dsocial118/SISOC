from sentry.services import get_sentry_frontend_config


def sentry_frontend(_request):
    return {"sentry_frontend": get_sentry_frontend_config()}
