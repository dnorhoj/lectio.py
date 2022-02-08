from datetime import datetime
import re
import requests
from bs4 import BeautifulSoup
from . import exceptions


class Module:
    """Lectio module object

    Represents a lectio module

    Args:
        title (str): Optional description of module (not present in all modules)
        subject (str): "Hold" from lectio, bascially which subject.
            Example: `1.a Da`
        teacher (str): Initials of teacher.
            Example: `abcd`
        room (str): Room name of module.
            Example: `0.015`
        extra_info (str): Extra info from module, includes homework and other info.
        start_time (:class:`datetime.datetime`): Start time of module
        end_time (:class:`datetime.datetime`): End time of module
        is_cancelled (bool): True if the module is cancelled
    """

    def __init__(self, **kwargs) -> None:
        self.title = kwargs.get("title")
        self.subject = kwargs.get("subject")
        self.teacher = kwargs.get("teacher")
        self.room = kwargs.get("room")
        self.extra_info = kwargs.get("extra_info")
        self.start_time = kwargs.get("start_time")
        self.end_time = kwargs.get("end_time")
        self.is_cancelled = kwargs.get("is_cancelled")


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
        self.__INST_ID = inst_id
        self.__BASE_URL = f"https://www.lectio.dk/lectio/{str(inst_id)}"
        self.__CREDS = []

        self.__session = requests.Session()
        # TODO: Check if inst_id is valid

    def authenticate(self, username: str, password: str, save_creds: bool = True) -> bool:
        """Authenticates you on Lectio.

        Note:
            Functionality is not completely implemented.
            Cannot check if authentication was successfull.

        Note:
            Running :py:func:`authenticate` on an already authenticated object
            will log you out of the already authenticated user.

            This will happen even though authentication was unsuccessful.

        Args:
            username (str): Lectio username for the given institution id.
            password (str): Lectio password for the given institution id.
            save_creds (bool): Whether the credentials should be saved in the object (useful for auto relogin on logout)

        Raises:
            lectio.IncorrectCredentialsError: When incorrect credentials passed

        Example::

            from lectio import Lectio

            lect = Lectio(123)

            if lect.authenticate("username", "password"):
                print("Authenticated")
            else:
                print("Not authenticated")
        """

        self.__CREDS = []
        if save_creds:
            self.__CREDS = [username, password]

        # Call the actual authentication method
        self._authenticate(username, password)

        # Check if authentication passed
        self._request(self.__BASE_URL + "/forside.aspx")

    def _authenticate(self, username: str = None, password: str = None) -> bool:
        if username is None or password is None:
            if len(self.__CREDS) != 2:
                raise exceptions.UnauthenticatedError(
                    "Auto auth failed, did you authenticate?")

            username, password = self.__CREDS

        self.log_out()  # Clear session

        login_page = self.__session.get(self.__BASE_URL + "/login.aspx")

        if login_page.status_code != 200:
            return False

        parser = BeautifulSoup(login_page.text, "html.parser")

        self.__session.post(
            self.__BASE_URL + "/login.aspx",
            data={
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
            }
        )

    def get_user_id(self) -> int:
        """Gets your user id

        Returns:
            int: User id
        """

        r = self._request(self.__BASE_URL + "/forside.aspx")

        soup = BeautifulSoup(r.text, 'html.parser')

        content = soup.find(
            'meta', {'name': 'msapplication-starturl'}).attrs.get('content')

        user_id = int(re.match(r'.*id=([0-9]+)$', content)[1])

        return user_id

    def get_schedule_for_student(self, elevid: int, weekno: int = None) -> any:
        """Get lectio schedule for current or specific week.

        Get all modules for a week.

        Parameters:
            elevid (int): Student id
            weekno (int): Week number

        Returns:
            list: Two dimensional list which contains all the days of the week, and all the corresponding modules for each day.
        """

        schedule_request = self._request(
            f"{self.__BASE_URL}/SkemaNy.aspx?type=elev&elevid={str(elevid)}")

        soup = BeautifulSoup(schedule_request.text, 'html.parser')
        days = soup.find_all(
            "div", class_="s2skemabrikcontainer lec-context-menu-instance")

        schedule = []
        for day in days:
            day_list = []
            for module_soup in day.findChildren("a", recursive=False):
                day_list.append(self._parse_module(module_soup))
            schedule.append(day_list)

        return schedule

    def _parse_module(self, module_soup) -> Module:
        module = Module()

        unparsed_module = module_soup["data-additionalinfo"]

        # Find module name
        title = module_soup.find(
            'span', attrs={"style": "word-wrap:break-word;"})

        module.title = title.text if title else None

        # Parse time
        unparsed_time = re.search(
            r"([0-9]{1,2}\/[0-9]{1,2}-[0-9]{4} )([0-9]{2}:[0-9]{2}) til ([0-9]{2}:[0-9]{2})", unparsed_module)

        if unparsed_time:
            module.start_time = datetime.strptime(
                unparsed_time[1] + unparsed_time[2], "%d/%m-%Y %H:%M")
            module.end_time = datetime.strptime(
                unparsed_time[1] + unparsed_time[3], "%d/%m-%Y %H:%M")

        # Parse subject
        subject = re.search(r"Hold: (.*)", unparsed_module)
        module.subject = subject[1] if subject else None

        # Parse teacher
        teacher = re.search(r"Lærer: (.*)", unparsed_module)
        if not teacher:
            teacher = re.search(r"Lærere: (.*)", unparsed_module)

        module.teacher = teacher[1] if teacher else None

        # Parse room
        room = re.search(r"Lokale: (.*)", unparsed_module)
        if not room:
            room = re.search(r"Lokaler: (.*)", unparsed_module)

        module.room = room[1] if room else None

        # Parse if module is cancelled
        module.is_cancelled = 's2cancelled' in module_soup['class']

        # TODO: Parse extra info

        return module

    def _request(self, url: str, method: str = "GET", **kwargs) -> requests.Response:
        r = self.__session.request(method, url, **kwargs)

        if f"{self.__INST_ID}/login.aspx?prevurl=" in r.url:
            self._authenticate()
            r = self.__session.get(url)
            if f"{self.__INST_ID}/login.aspx?prevurl=" in r.url:
                raise exceptions.IncorrectCredentialsError(
                    "Could not restore session, probably incorrect credentials")

        return r

    def log_out(self) -> None:
        """Clears entire session, thereby logging you out

        Returns:
            None
        """
        self.__session = requests.Session()
