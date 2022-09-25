import re
from datetime import datetime, timedelta
from typing import TYPE_CHECKING, List
from bs4 import BeautifulSoup

if TYPE_CHECKING:
    from ..lectio import Lectio


class Module:
    """Lectio module object

    Represents a lectio module

    Args:
        title (str|None): Optional description of module (not present in all modules)
        subject (str|None): "Hold" from lectio, bascially which subject.
            Example: `1.a Da`
        teacher (str|None): Initials of teacher.
            Example: `abcd`
        room (str|None): Room name of module.
            Example: `0.015`
        extra_info (str|None): Extra info from module, includes homework and other info.
        start_time (:class:`datetime.datetime`): Start time of module
        end_time (:class:`datetime.datetime`): End time of module
        status (int): 0=normal, 1=changed, 2=cancelled
        url (str|None): Url for more info for the module
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

    def __repr__(self) -> str:
        return f"Module({self.subject}, {self.start_time}, {self.end_time})"

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


def get_schedule(lectio: 'Lectio', params: List[str], start_date: datetime, end_date: datetime, strip_time: bool = True) -> List[Module]:
    """Get lectio schedule for current or specific week.

    Get all modules in specified time range.

    Parameters:
        lectio (:class:`lectio.Lectio`): Base lectio object
        params (list): List of get parameters to add to request
        start_date (:class:`datetime.datetime`): Start date
        end_date (:class:`datetime.datetime`): End date
        strip_time (bool): Whether to remove hours, minutes and seconds from date info, also adds 1 day to end time.
            Basically just allows you to put in a random time of two days, and still get all modules from all the days including start and end date.

    Returns:
        List[:class:`lectio.Module`]: List containing all modules in specified time range.
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

    params = "&".join([
        "type=ShowListAll",
        f"starttime={start_date}",
        f"endtime={end_date}",
        "dagsbemaerk=0",
        *params
    ])

    schedule_request = lectio._request(f"SkemaAvanceret.aspx?{params}")

    soup = BeautifulSoup(schedule_request.text, 'html.parser')

    modules = soup.find(
        "table", class_="list texttop lf-grid").findChildren('tr', class_=None)

    schedule = []
    for module in modules:
        a = module.findChild('a')
        module = parse_additionalinfo(
            a.attrs.get('data-additionalinfo'))

        # Add href to module
        href = a.attrs.get('href')
        if href:
            module.url = f"https://www.lectio.dk{href}"

        schedule.append(module)

    return schedule


def parse_additionalinfo(info: str) -> Module:
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


def get_sched_for_student(lectio: 'Lectio', student_id: int, start_date: datetime, end_date: datetime, strip_time: bool = True) -> List[Module]:
    return get_schedule(lectio, [f"studentsel={student_id}"], start_date, end_date, strip_time)
