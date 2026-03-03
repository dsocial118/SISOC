import sentry_sdk


class SentryUserContextMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = getattr(request, "user", None)
        if user is not None and getattr(user, "is_authenticated", False):
            sentry_sdk.set_user(
                {
                    "id": str(user.pk),
                    "username": user.get_username(),
                }
            )
        else:
            sentry_sdk.set_user(None)

        return self.get_response(request)
