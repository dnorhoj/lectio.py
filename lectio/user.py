from bs4 import BeautifulSoup
from typing import TYPE_CHECKING, List

from .helpers.schedule import get_sched_for_student, get_sched_for_teacher

if TYPE_CHECKING:
    from datetime import datetime
    from .helpers.schedule import Module
    from .lectio import Lectio


class UserType:
    """User types

    Attributes:
        STUDENT (int): Student
        TEACHER (int): Teacher

    Example:
        >>> from lectio import Lectio
        >>> from lectio.user import UserType
        >>> lec = Lectio(123)
        >>> lec.authenticate("username", "password")
        >>> me = lec.me()
        >>> print(me.type)
        0
        >>> print(me.type == UserType.STUDENT)
        True
    """

    STUDENT = 0
    TEACHER = 1


class User:
    """Lectio user object

    Represents a lectio user

    Args:
        lectio (:class:`lectio.Lectio`): Lectio object
        user_id (int): User id
        user_type (int): User type (UserType.STUDENT or UserType.TEACHER)

    Attributes:
        id (int): User id
        type (int): User type (UserType.STUDENT or UserType.TEACHER)
        name (str): Name of user
        initials (str|None): Initials of user if user is a teacher
        class_name (str|None): Class of user if user is a student
        image (str): User image url
    """

    def __init__(self, lectio: 'Lectio', user_id: int, user_type: int = UserType.STUDENT) -> None:
        self._lectio = lectio
        self.id = user_id

        if not user_type in [UserType.STUDENT, UserType.TEACHER]:
            raise ValueError("Invalid user type")

        self.type = user_type
        self.__populate()

        # TODO; Don't know if user exist check should be here or in lectio.py

    def __populate(self) -> None:
        """Populate user object

        Populates the user object with data from lectio, such as name, class name, etc.
        """

        params = ""
        if self.type == UserType.STUDENT:
            params = f"type=elev&elevid={self.id}"
        elif self.type == UserType.TEACHER:
            params = f"type=laerer&laererid={self.id}"

        r = self._lectio._request(f"SkemaNy.aspx?{params}")

        soup = BeautifulSoup(r.text, "html.parser")

        title = soup.find("div", {"id": "s_m_HeaderContent_MainTitle"}).text

        title = " ".join(title.split()[1:])

        if self.type == UserType.STUDENT:
            self.name = title.split(", ")[0]
            self.class_name = title.split(", ")[1].split(" - ")[0]
        elif self.type == UserType.TEACHER:
            self.initials, self.name, *_ = title.split(" - ")

        src = soup.find(
            "img", {"id": "s_m_HeaderContent_picctrlthumbimage"}).get("src")

        self.image = f"https://www.lectio.dk{src}&fullsize=1"

    def get_schedule(self, start_date: 'datetime', end_date: 'datetime', strip_time: bool = True) -> List['Module']:
        """Get schedule for user

        Args:
            start_date (:class:`datetime.datetime`): Start date
            end_date (:class:`datetime.datetime`): End date
            strip_time (bool): Strip time from datetime objects (default: True)
        """

        if self.type == UserType.STUDENT:
            return get_sched_for_student(self._lectio, self.id, start_date, end_date, strip_time)
        elif self.type == UserType.TEACHER:
            return get_sched_for_teacher(self._lectio, self.id, start_date, end_date, strip_time)

    def __repr__(self) -> str:
        type_str = "Student" if self.type == UserType.STUDENT else "Teacher"
        return f"User({type_str}, {self.id})"
