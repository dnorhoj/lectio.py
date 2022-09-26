import re
import requests
from bs4 import BeautifulSoup

from . import exceptions

from .user import User, UserType
from .school import School


class Lectio:
    """The main Lectio class.

    A Lectio object is your gateway to manipulating and getting data from Lectio.

    Args:
        inst_id (int): Your Lectio institution id.

            You can find this by going to your institution's Lectio login
            page and it should be in the URL like this::

                https://www.lectio.dk/lectio/123/login.aspx

            Here, the `123` would be my institution id.
    """

    def __init__(self, inst_id: int) -> None:
        self.__CREDS = []
        self.__session = requests.Session()

        self.inst_id = inst_id

    def authenticate(self, username: str, password: str, save_creds: bool = True) -> bool:
        """Authenticates you on Lectio.

        Note:
            Running :py:func:`authenticate` on an already authenticated object
            will log you out of the already authenticated user.

            This will happen even though authentication was unsuccessful.

        Args:
            username (str): Lectio username for the given institution id.
            password (str): Lectio password for the given institution id.
            save_creds (bool): Whether the credentials should be saved in the object (useful for auto relogin on logout)

        Raises:
            :class:`exceptions.IncorrectCredentialsError`: When incorrect credentials passed
            :class:`exceptions.InstitutionDoesNotExistError`: When the institution id passed on creation of object is invalid

        Example::

            from lectio import Lectio, exceptions

            lect = Lectio(123)

            try:
                lect.authenticate("username", "password")
                print("Authenticated")
            except exceptions.IncorrectCredentialsError:
                print("Not authenticated")
        """

        self.__CREDS = []
        if save_creds:
            self.__CREDS = [username, password]

        # Call the actual authentication method
        self._authenticate(username, password)

    def _authenticate(self, username: str = None, password: str = None):
        if username is None or password is None:
            if len(self.__CREDS) != 2:
                raise exceptions.UnauthenticatedError(
                    "No authentication details provided and no saved credentials found!")

            username, password = self.__CREDS

        self.log_out()  # Clear session

        URL = f"https://www.lectio.dk/lectio/{self.inst_id}/login.aspx"

        login_page = self.__session.get(URL)

        if 'fejlhandled.aspx?title=Skolen+eksisterer+ikke' in login_page.url:
            raise exceptions.InstitutionDoesNotExistError(
                f"The institution with the id '{self._INST_ID}' does not exist!")

        parser = BeautifulSoup(login_page.text, "html.parser")

        r = self.__session.post(URL, data={
            "time": 0,
            "__EVENTTARGET": "m$Content$submitbtn2",
            "__EVENTARGUMENT": "",
            "__SCROLLPOSITION": "",
            "__VIEWSTATEX": parser.find(attrs={"name": "__VIEWSTATEX"})["value"],
            "__VIEWSTATEY_KEY": "",
            "__VIEWSTATE": "",
            "__EVENTVALIDATION": parser.find(attrs={"name": "__EVENTVALIDATION"})["value"],
            "m$Content$username": username,
            "m$Content$password": password
        })

        if r.url == URL:
            # Authentication failed
            raise exceptions.IncorrectCredentialsError(
                "Incorrect credentials provided!")

    @property
    def school(self) -> School:
        """:class:`lectio.school.School`: The school object for the authenticated user."""

        return School(self)

    def me(self) -> User:
        """Gets own user object

        Returns:
            :class:`lectio.profile.User`: User object
        """

        r = self._request("forside.aspx")

        soup = BeautifulSoup(r.text, 'html.parser')

        content = soup.find(
            'meta', {'name': 'msapplication-starturl'}).attrs.get('content')

        user_id = re.match(r'.*id=([0-9]+)$', content)[1]

        return self.get_user(user_id, check=False)

    def get_user(self, user_id: str, user_type: int = UserType.STUDENT, check: bool = True) -> User:
        """Gets a user by their id

        Args:
            user_id (str): The id of the user
            user_type (int): The type of the user (student or teacher)
            check (bool): Whether to check if the user exists

        Returns:
            :class:`lectio.profile.User`: User object

        Raises:
            :class:`lectio.exceptions.UserDoesNotExistError`: When the user does not exist
        """

        if check:
            type_str = "elev" if user_type == UserType.STUDENT else "laerer"

            # Check if user exists
            r = self._request(
                f"SkemaNy.aspx?type={type_str}&{type_str}id={user_id}")

            soup = BeautifulSoup(r.text, 'html.parser')

            if soup.title.string.strip().startswith("Fejl - Lectio"):
                raise exceptions.UserDoesNotExistError(
                    f"The user with the id '{user_id}' does not exist!")

        return User(self, user_id, user_type)

    def _request(self, url: str, method: str = "GET", **kwargs) -> requests.Response:
        r = self.__session.request(
            method, f"https://www.lectio.dk/lectio/{str(self.inst_id)}/{url}", **kwargs)

        if f"{self.inst_id}/login.aspx?prevurl=" in r.url:
            if not self._authenticate():
                raise exceptions.UnauthenticatedError("Unauthenticated")
            r = self.__session.get(
                f"https://www.lectio.dk/lectio/{str(self.inst_id)}/{url}")
            if f"{self.inst_id}/login.aspx?prevurl=" in r.url:
                raise exceptions.IncorrectCredentialsError(
                    "Could not restore session, probably incorrect credentials")

        return r

    def log_out(self) -> None:
        """Clears entire session, thereby logging you out

        Returns:
            None
        """
        self.__session = requests.Session()
