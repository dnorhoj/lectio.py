"""Here are all the custom Lectio.py exceptions as well as their explanation"""


class LectioError(Exception):
    """Base lectio.py exception"""


class UnauthenticatedError(LectioError):
    """Throws when trying to get data while unauthenticated or session expired"""


class IncorrectCredentialsError(LectioError):
    """Incorrect credentials error, mostly thrown in auto-login on session expired"""


class InstitutionDoesNotExistError(LectioError):
    """The institution with the id you provided does not exist."""

class UserDoesNotExistError(LectioError):
    """The user does not exist."""