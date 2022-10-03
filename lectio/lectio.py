import re
import requests
from bs4 import BeautifulSoup

from . import exceptions

from .models.user import Me, UserType
from .models.school import School


class Lectio:
    """The main Lectio class.

    A Lectio object is your gateway to manipulating and getting data from Lectio.

    Args:
        inst_id (int): Your Lectio institution id.

            You can find this by going to your institution's Lectio login
            page and it should be in the URL like this::

                https://www.lectio.dk/lectio/123/login.aspx

            Here, the ``123`` would be my institution id.

        username (str): Lectio username for the given institution id.
        password (str): Lectio password for the given institution id.
    """

    __school: School = None
    __me: Me = None

    def __init__(self, inst_id: int, username: str, password: str) -> None:
        self.__session = requests.Session()

        self.inst_id = inst_id
        self.__CREDS = [username, password]

        self._authenticate(username, password)

        self.__CREDS = []

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

    def me(self) -> Me:
        """Gets the authenticated user

        Returns:
            :class:`lectio.models.user.Me`: Own user object
        """

        if self.__me is None:
            r = self._request("forside.aspx")

            soup = BeautifulSoup(r.text, 'html.parser')

            content = soup.find(
                'meta', {'name': 'msapplication-starturl'}).attrs.get('content')

            user_id = re.match(r'.*id=([0-9]+)$', content)[1]

            # TODO; Add support for teachers
            self.__me = Me(self, user_id, UserType.STUDENT)

        return self.__me

    def get_school(self) -> School:
        """Gets the school object for the authenticated user

        This loads the school object, which gets cached for future use.

        Returns:
            :class:`lectio.models.school.School`: School object
        """

        if self.__school is None:
            self.__school = School(self)

        return self.__school

    def _request(self, url: str, method: str = "GET", full_url: bool = False, **kwargs) -> requests.Response:
        if not full_url:
            url = f"https://www.lectio.dk/lectio/{str(self.inst_id)}/{url}"

        r = self.__session.request(
            method, url, **kwargs)

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
