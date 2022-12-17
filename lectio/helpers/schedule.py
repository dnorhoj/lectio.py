import re
from datetime import datetime, timedelta
from typing import TYPE_CHECKING, List
from bs4 import BeautifulSoup
from enum import Enum

from ..models.module import Module

if TYPE_CHECKING:
    from ..lectio import Lectio


class ModuleStatus(Enum):
    """Module status enum"""

    NORMAL = 0
    """Module has not been changed"""

    CHANGED = 1
    """Module has been changed (is green in lectio)"""

    CANCELLED = 2
    """Module has been cancelled (is red in lectio)"""

    def __str__(self) -> str:
        if self.value == self.NORMAL.value:
            return "normal"
        elif self.value == self.CHANGED.value:
            return "changed"
        elif self.value == self.CANCELLED.value:
            return "cancelled"


def get_schedule(lectio: 'Lectio', params: List[str], start_date: datetime, end_date: datetime, strip_time: bool = True) -> List[Module]:
    """Get lectio schedule for current or specific week.

    Get all modules in specified time range.

    Parameters:
        lectio (Lectio): Base lectio object
        params (list): List of get parameters to add to request
        start_date (:class:`datetime.datetime`): Start date
        end_date (:class:`datetime.datetime`): End date
        strip_time (bool): Whether to remove hours, minutes and seconds from date info, also adds 1 day to end time.
            Basically just allows you to put in a random time of two days, and still get all modules from all the days including start and end date.

    Returns:
        List[Module]: List containing all modules in specified time range.
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

    module_table = soup.find(
        "table", class_="list texttop lf-grid")

    if not module_table:
        return []

    # Not a good way of checking if there are no modules, but it works
    if module_table.find("div", {"class": "noRecord"}):
        return []

    modules = module_table.findChildren('tr', class_=None)

    schedule = []
    for module in modules:
        a = module.findChild('a')
        module = parse_additionalinfo(
            lectio, a.attrs.get('data-additionalinfo'))

        # Add href to module
        href = a.attrs.get('href')
        if href:
            module.url = f"https://www.lectio.dk{href}"

        schedule.append(module)

    return schedule


def parse_additionalinfo(lectio: 'Lectio', info: str) -> Module:
    module = Module(lectio)

    info_list = info.split('\n')

    # Parse module status
    if info_list[0] == 'Ændret!':
        module.status = ModuleStatus.CHANGED
        info_list.pop(0)
    elif info_list[0] == 'Aflyst!':
        module.status = ModuleStatus.CANCELLED
        info_list.pop(0)
    else:
        module.status = ModuleStatus.NORMAL

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
