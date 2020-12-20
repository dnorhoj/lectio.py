import requests
from bs4 import BeautifulSoup

class Lectio:
    """The main Lectio class.

    A Lectio object is your gateway to manipulating and getting data from Lectio.

    Args:
        inst_id (int): Your Lectio institution id.

            You can find this by going to your institution's Lectio login page and it should be in the URL like this::

                https://www.lectio.dk/lectio/123/login.aspx

            Here, the `123` would be my institution id.
    """

    def __init__(self, inst_id: int):
        self.__inst_id = inst_id
        self.__base_url = f"https://www.lectio.dk/lectio/{str(inst_id)}"
        self.__session = requests.Session()

    def authenticate(self, username: str, password: str) -> bool:
        """Authenticates you on Lectio.

        Example::

            from lectiotools import Lectio

            lect = Lectio(123)

            if lect.authenticate("username", "password"):
                print("Authenticated")
            else:
                print("Not authenticated")

        Note:
            Running :py:func:`authenticate` on an already authenticated object
            will log you out of the already authenticated user.

            This will happen even though authentication was unsuccessful.

        Args:
            username (str): Lectio username for the given institution id.
            password (str): Lectio password for the given institution id.

        Returns:
            bool: Whether authentication was succesful or not.
        """

        self.log_out()

        login_page = self.__session.get(self.__base_url+"/login.aspx")

        if login_page.status_code != 200:
            return False

        parser = BeautifulSoup(login_page.text, "html.parser")

        res = self.__session.post(
            self.__base_url+"/login.aspx",
            data={
                "time": 0,
                "__EVENTTARGET": "m$Content$submitbtn2",
                "__EVENTARGUMENT": "",
                "__SCROLLPOSITION": "",
                "__VIEWSTATEX": parser.find(attrs={"name":"__VIEWSTATEX"})["value"],
                "__VIEWSTATEY_KEY": "",
                "__VIEWSTATE": "",
                "__EVENTVALIDATION": parser.find(attrs={"name":"__EVENTVALIDATION"})["value"],
                "m$Content$username": username,
                "m$Content$password": password
            }
        )

        return True

    def log_out(self):
        return self.__session.get(self.__base_url+"/logout.aspx")

    def get_schedule(self, student_id):
        pass