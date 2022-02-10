class LectioError(Exception):
    """Base lectio.py exception"""


class UnauthenticatedError(LectioError):
    """Throws when trying to get data while unauthenticated or session expired"""


class IncorrectCredentialsError(LectioError):
    """Incorrect credentials error, mostly thrown in auto-login on session expired"""
