from enum import Enum
from bs4 import BeautifulSoup
from typing import TYPE_CHECKING, List

from ..helpers.schedule import get_schedule

if TYPE_CHECKING:
    from datetime import datetime
    from ..helpers.schedule import Module
    from ..lectio import Lectio


class UserType(Enum):
    """User types enum

    Example:
        >>> from lectio import Lectio
        >>> from lectio.models.user import UserType
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

    def get_str(self) -> str:
        """Get string representation of user type for lectio interface in english

        Returns:
            str: String representation of user type
        """

        if self.value == self.STUDENT.value:
            return "student"
        elif self.value == self.TEACHER.value:
            return "teacher"

    def __str__(self) -> str:
        if self.value == self.STUDENT.value:
            return "elev"
        elif self.value == self.TEACHER.value:
            return "laerer"


class User:
    """Lectio user object

    Represents a lectio user

    Note:
        This class should not be instantiated directly,
        but rather through the :meth:`lectio.Lectio.get_user`
        or :meth:`lectio.school.School.search_for_users` methods or similar.

    Args:
        lectio (:class:`lectio.Lectio`): Lectio object
        user_id (int): User id
        user_type (:class:`lectio.models.user.UserType`): User type (UserType.STUDENT or UserType.TEACHER)
        lazy (bool): Whether to not populate user object on instantiation (default: False)

    Attributes:
        id (int): User id
        type (:class:`lectio.models.user.UserType`): User type (UserType.STUDENT or UserType.TEACHER)
    """

    __name = None
    __initials = None
    __class_name = None
    __image = None

    def __init__(self, lectio: 'Lectio', user_id: int, user_type: UserType = UserType.STUDENT, *, lazy=False, **user_data) -> None:
        self._lectio = lectio
        self.id = user_id

        self.type = user_type

        if not lazy:
            self.__populate()
        else:
            self.__name = user_data.get("name")
            self.__initials = user_data.get("initials")
            self.__class_name = user_data.get("class_name")
            self.__image = user_data.get("image")

    def __populate(self) -> None:
        """Populate user object

        Populates the user object with data from lectio, such as name, class name, etc.
        """

        # TODO; Check if user is student or teacher

        # Get user's schedule for today
        r = self._lectio._request(
            f"SkemaNy.aspx?type={self.type}&{self.type}id={self.id}")

        soup = BeautifulSoup(r.text, "html.parser")

        title = soup.find("div", {"id": "s_m_HeaderContent_MainTitle"}).text

        title = " ".join(title.split()[1:])

        if self.type == UserType.STUDENT:
            self.__name = title.split(", ")[0]
            self.__class_name = title.split(", ")[1].split(" - ")[0]
        elif self.type == UserType.TEACHER:
            self.__initials, self.__name, *_ = title.split(" - ")

        src = soup.find(
            "img", {"id": "s_m_HeaderContent_picctrlthumbimage"}).get("src")

        self.__image = f"https://www.lectio.dk{src}&fullsize=1"

    def get_schedule(self, start_date: 'datetime', end_date: 'datetime', strip_time: bool = True) -> List['Module']:
        """Get schedule for user

        Args:
            start_date (:class:`datetime.datetime`): Start date
            end_date (:class:`datetime.datetime`): End date
            strip_time (bool): Strip time from datetime objects (default: True)
        """

        return get_schedule(
            self._lectio,
            [f"{self.type.get_str()}sel={self.id}"],
            start_date,
            end_date,
            strip_time
        )

    def __repr__(self) -> str:
        return f"User({self.type.get_str().capitalize()}, {self.id})"

    @property
    def name(self) -> str:
        """str: User's name"""

        if not self.__name:
            self.__populate()

        return self.__name

    @property
    def image(self) -> str:
        """str: User's image url"""

        if not self.__image:
            self.__populate()

        return self.__image

    @property
    def initials(self) -> str:
        """str|None: User's initials (only for teachers)"""

        if self.type == UserType.STUDENT:
            return None

        if not self.__initials:
            self.__populate()

        return self.__initials

    @property
    def class_name(self) -> str:
        """str|None: User's class name (only for students)"""

        if self.type == UserType.TEACHER:
            return None

        if not self.__class_name:
            self.__populate()

        return self.__class_name

    def __eq__(self, __o: object) -> bool:
        if not isinstance(__o, User):
            return False

        return self.id == __o.id and self.type == __o.type


class Me(User):
    # TODO: Add methods for getting grades, absences, etc.
    pass
