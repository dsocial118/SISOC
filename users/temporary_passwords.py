"""Helpers para exponer contraseñas temporales solo en la sesión del admin."""

TEMP_PASSWORD_SESSION_KEY = "users_temporary_passwords"


def _get_password_map(session) -> dict[str, str]:
    raw_data = session.get(TEMP_PASSWORD_SESSION_KEY, {})
    if not isinstance(raw_data, dict):
        return {}
    return {str(key): str(value) for key, value in raw_data.items() if value}


def store_temporary_password(session, *, user_id: int, password: str) -> None:
    password_map = _get_password_map(session)
    password_map[str(user_id)] = password
    session[TEMP_PASSWORD_SESSION_KEY] = password_map
    session.modified = True


def get_temporary_password(session, *, user_id: int) -> str | None:
    return _get_password_map(session).get(str(user_id))


def clear_temporary_password(session, *, user_id: int) -> None:
    password_map = _get_password_map(session)
    removed = password_map.pop(str(user_id), None)
    if removed is None and TEMP_PASSWORD_SESSION_KEY not in session:
        return
    if password_map:
        session[TEMP_PASSWORD_SESSION_KEY] = password_map
    else:
        session.pop(TEMP_PASSWORD_SESSION_KEY, None)
    session.modified = True
