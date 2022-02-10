from datetime import datetime, timedelta
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
        status (int): 0=normal, 1=changed, 2=cancelled
        url (str): Url for more info for the module
    """

    def __init__(self, **kwargs) -> None:
        self.title = kwargs.get("title")
        self.subject = kwargs.get("subject")
        self.teacher = kwargs.get("teacher")
        self.room = kwargs.get("room")
        self.extra_info = kwargs.get("extra_info")
        self.start_time = kwargs.get("start_time")
        self.end_time = kwargs.get("end_time")
        self.status = kwargs.get("status")
        self.url = kwargs.get("url")

    def display(self):
        print(f"Title:      {self.title}")
        print(f"Subject(s): {self.subject}")
        print(f"Teacher(s): {self.teacher}")
        print(f"Room(s):    {self.room}")
        print(f"Starts at:  {self.start_time}")
        print(f"Ends at:    {self.end_time}")
        print(f"Status:     {self.status}")
        print(f"URL:        {self.url}")
        print(f"Extra info:\n\n{self.extra_info}")


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

    def get_schedule_for_student(self, elevid: int, start_date: datetime, end_date: datetime, strip_time: bool = True) -> any:
        """Get lectio schedule for current or specific week.

        Get all modules in specified time range.

        Parameters:
            elevid (int): Student id
            start_date (:class:`datetime.datetime`): Start date
            end_date (:class:`datetime.datetime`): End date
            strip_time (bool): Whether to remove hours, minutes and seconds from date info, also adds 1 day to end time.
                Basically just allows you to put in a random time of two days, and still get all modules from all the days including start and end date.

        Returns:
            list: List containing all modules in specified time range.
        """

        replacetime = {}
        if strip_time:
            end_date = end_date + timedelta(days=1)
            replacetime = {
                "hour": 0,
                "minute": 0,
                "second": 0,
            }

        start_date = start_date.replace(
            **replacetime, microsecond=0).isoformat()
        end_date = end_date.replace(**replacetime, microsecond=0).isoformat()

        params = (
            "type=ShowListAll&"
            f"starttime={start_date}&"
            f"endtime={end_date}&"
            "dagsbemaerk=0&"
            f"studentsel={elevid}"
        )

        schedule_request = self._request(
            f"{self.__BASE_URL}/SkemaAvanceret.aspx?{params}")

        soup = BeautifulSoup(schedule_request.text, 'html.parser')

        modules = soup.find(
            "table", class_="list texttop lf-grid").findChildren('tr', class_=None)

        schedule = []
        for module in modules:
            a = module.findChild('a')
            module = self._parse_additionalinfo(
                a.attrs.get('data-additionalinfo'))
            module.url = f"https://www.lectio.dk{a.attrs.get('href')}"
            schedule.append(module)

        return schedule

    def _parse_additionalinfo(self, info: str) -> Module:
        module = Module()

        info_list = info.split('\n')

        # Parse module status
        if info_list[0] == 'Ændret!':
            module.status = 1
            info_list.pop(0)
        elif info_list[0] == 'Aflyst!':
            module.status = 2
            info_list.pop(0)
        else:
            module.status = 0

        # Parse title
        if not re.match(r'^[0-9]{1,2}\/[0-9]{1,2}-[0-9]{4} [0-9]{2}:[0-9]{2}', info_list[0]):
            module.title = info_list[0]
            info_list.pop(0)

        # Parse time
        times = info_list[0].split(" til ")
        info_list.pop(0)
        module.start_time = datetime.strptime(times[0], "%d/%m-%Y %H:%M")
        if len(times[1]) == 5:
            module.end_time = datetime.strptime(
                times[0][:-5] + times[1], "%d/%m-%Y %H:%M")
        else:
            module.end_time = datetime.strptime(times[1], "%d/%m-%Y %H:%M")

        # Parse subject(s)
        subject = re.search(r"Hold: (.*)", info)
        if subject:
            info_list.pop(0)
            module.subject = subject[1]

        # Parse teacher(s)
        teacher = re.search(r"Lærere?: (.*)", info)
        if teacher:
            info_list.pop(0)
            module.teacher = teacher[1]

        # Parse room(s)
        room = re.search(r"Lokaler?: (.*)", info)
        if room:
            info_list.pop(0)
            module.room = room[1]

        # Put any additional info into extra_info
        if info_list:
            info_list.pop(0)
            module.extra_info = "\n".join(info_list)

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
