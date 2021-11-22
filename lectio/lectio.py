import requests
import re
from datetime import datetime
from bs4 import BeautifulSoup


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
    """

    def __init__(self, **kwargs) -> None:
        self.title = kwargs.get("title")
        self.subject = kwargs.get("subject")
        self.teacher = kwargs.get("teacher")
        self.room = kwargs.get("room")
        self.extra_info = kwargs.get("extra_info")
        self.start_time = kwargs.get("start_time")
        self.end_time = kwargs.get("end_time")


class Lectio:
    """The main Lectio class.

    A Lectio object is your gateway to manipulating and getting data from Lectio.

    Args:
        inst_id (int): Your Lectio institution id.

            You can find this by going to your institution's Lectio login page and it should be in the URL like this::

                https://www.lectio.dk/lectio/123/login.aspx

            Here, the `123` would be my institution id.
    """

    def __init__(self, inst_id: int) -> None:
        self.__INST_ID = inst_id
        self.__BASE_URL = f"https://www.lectio.dk/lectio/{str(inst_id)}"

        self.__session = requests.Session()
        # TODO: Check if inst_id is valid

    def authenticate(self, username: str, password: str) -> bool:
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

        Returns:
            bool: Whether authentication was succesful or not.

        Example::

            from lectiotools import Lectio

            lect = Lectio(123)

            if lect.authenticate("username", "password"):
                print("Authenticated")
            else:
                print("Not authenticated")
        """

        self.log_out()

        login_page = self.__session.get(self.__BASE_URL+"/login.aspx")

        if login_page.status_code != 200:
            return False

        parser = BeautifulSoup(login_page.text, "html.parser")

        res = self.__session.post(
            self.__BASE_URL+"/login.aspx",
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

        # TODO: Check if login was successfull

        return True

    def get_schedule_for_student(self, elevid: int, weekno: int = None) -> Module:
        """Get lectio schedule for current or specific week.

        Get all modules for a week.

        Parameters:
            elevid (int): Student id
            weekno (int): Week number

        Returns:
            list: Two dimensional list which contains all the days of the week, and all the corresponding modules for each day.
        """

        schedule_request = self._get(
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
                unparsed_time[1]+unparsed_time[2], "%d/%m-%Y %H:%M")
            module.end_time = datetime.strptime(
                unparsed_time[1]+unparsed_time[3], "%d/%m-%Y %H:%M")
        
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

        # TODO: Parse extra info

        return module

    def _get(self, url: str) -> requests.Response:
        return self.__session.get(url)

    def log_out(self) -> None:
        """Clears entire session, thereby logging you out

        Returns:
            None
        """
        self.__session = requests.Session()
