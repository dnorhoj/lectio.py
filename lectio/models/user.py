from enum import Enum
from bs4 import BeautifulSoup
from typing import TYPE_CHECKING, List, Optional

from ..helpers.schedule import get_schedule

if TYPE_CHECKING:
    from datetime import datetime
    from ..lectio import Lectio
    from .module import Module

undef = object()


class UserType(Enum):
    """User types enum

    Example:
        >>> from lectio import Lectio
        >>> from lectio.models.user import UserType
        >>> lec = Lectio(123, "username", "password")
        >>> me = lec.me()
        >>> print(me.type)
        <UserType.STUDENT: 0>
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
        but rather through the :attr:`lectio.Lectio.me`
        or :meth:`lectio.models.school.School.search_for_users` methods or similar.

    Note:
        A :class:`lectio.models.user.User` object is a lazy object by default,
        which means that no data is fetched from lectio on instantiation.

        When you access any non-lazy attribute, the user object will be populated with data from lectio.

    Args:
        lectio (:class:`lectio.Lectio`): Lectio object
        user_id (int): User id
        user_type (:class:`lectio.models.user.UserType`): User type (UserType.STUDENT or UserType.TEACHER)
        lazy (bool): Whether to not populate user object on instantiation (default: True)

    Attributes:
        id (int): User id
        populated (bool): Whether user object has been populated with data from lectio
                          if this is False, the user object is a lazy object and only contains available data (often just name and id)
        type (:class:`lectio.models.user.UserType`): User type (UserType.STUDENT or UserType.TEACHER)
    """

    __class_name = None
    __image = None
    populated = False

    def __init__(self, lectio: 'Lectio', user_id: int, name: str, user_type: UserType = UserType.STUDENT, *, lazy=True, **kwargs) -> None:
        self._lectio = lectio

        self.id = user_id
        self.type = user_type
        self.name = name
        # Will be none if user is not teacher
        self.initials = kwargs.get('initials')

        # Populate ovject if specified as non-lazy
        if not lazy:
            self.populate()

    def populate(self) -> None:
        """Populate user object

        Populates the user object with data from lectio, such as name, class name, etc.
        """

        if self.populated:
            return

        self.populated = True

        # Get user's schedule for today
        r = self._lectio._request(
            f"SkemaNy.aspx?type={self.type}&{self.type}id={self.id}")

        soup = BeautifulSoup(r.text, "html.parser")

        title = soup.find("div", {"id": "s_m_HeaderContent_MainTitle"}).text

        title = " ".join(title.split()[1:])

        if self.type == UserType.STUDENT:
            name_class = title.split(", ")
            self.__name = name_class[0]

            # Check if user has a class
            if len(name_class) > 1:
                self.__class_name = title.split(", ")[1].split(" - ")[0]
            else:
                self.__class_name = None

        # elif self.type == UserType.TEACHER:
        #     self.__initials, self.__name, *_ = title.split(" - ")

        src = soup.find(
            "img", {"id": "s_m_HeaderContent_picctrlthumbimage"}).get("src")

        if "defaultfoto" not in src:
            self.__image = f"https://www.lectio.dk{src}&fullsize=1"

    def get_schedule(self, start_date: 'datetime', end_date: 'datetime', strip_time: bool = True) -> List['Module']:
        """Get schedule for user

        Note:
            As lectio is weird, you can only get a schedule for a range
            that is less than one month.
            If you specify a range greater than one month, you will get an empty return list.

        Args:
            start_date (:class:`datetime.datetime`): Start date
            end_date (:class:`datetime.datetime`): End date
            strip_time (bool): Whether to remove hours, minutes and seconds from date info, also adds 1 day to end time.
                Basically just allows you to put in a random time of two days, and still get all modules from all the days including start and end date.
        """

        return get_schedule(
            self._lectio,
            [f"{self.type.get_str()}sel={self.id}"],
            start_date,
            end_date,
            strip_time
        )

    def __repr__(self) -> str:
        return f"<User type={self.type.get_str().capitalize()} id={self.id}>"

    @property
    def url(self) -> str:
        """str: User's lectio url"""

        return f"https://www.lectio.dk/lectio/{self._lectio.inst_id}/SkemaNy.aspx?type={self.type}&{self.type}id={self.id}"

    def get_image_url(self) -> str:
        """Get user's image url

        Returns:
            str: User's image url
        """

        self.populate()

        return self.__image

    def get_class_name(self) -> Optional[str]:
        """Get user's class name

        Only for :class:`lectio.models.user.UserType.STUDENT`.

        Returns:
            str|None: Class name or ``None`` if user is :class:`lectio.models.user.UserType.TEACHER`.
        """

        if self.type == UserType.TEACHER:
            return None

        self.populate()

        return self.__class_name

    def __eq__(self, __o: object) -> bool:
        # Equality check

        if not isinstance(__o, User):
            return False

        return self.id == __o.id and self.type == __o.type


class Me(User):
    # TODO: Add methods for getting grades, absences, etc.
    pass
