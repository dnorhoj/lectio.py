from typing import TYPE_CHECKING, Generator, List
from bs4 import BeautifulSoup

from .user import User, UserType
from ..import exceptions
from .room import Room

if TYPE_CHECKING:
    from .. import Lectio


class School:
    """A school object.

    Represents a school.

    Note:
        This class should not be instantiated directly,
        but rather through the :meth:`lectio.Lectio.get_school` method.

    Args:
        lectio (:class:`lectio.Lectio`): Lectio object
    """

    students: List[User]
    teachers: List[User]
    groups: List[None]
    rooms: List[Room]
    name: str

    def __init__(self, lectio: 'Lectio') -> None:
        self._lectio = lectio
        self.__populate()

    def __populate(self) -> None:
        r = self._lectio._request("FindSkemaAdv.aspx")

        soup = BeautifulSoup(r.text, 'html.parser')

        self.name = soup.find(
            "div", {"id": "m_masterleftDiv"}).text.strip().split("\n")[0].replace("\r", "")

        # Get school's students
        self.students = []
        student_select = soup.find(
            "select", {"id": "m_Content_StudentMC_totalSet"})
        for user in student_select.find_all("option"):
            name = user.text.strip().split(" (")[0]

            self.students.append(
                User(self._lectio, int(user["value"][1:]), UserType.STUDENT, lazy=True, name=name))

        # Get school's teachers
        self.teachers = []
        teacher_select = soup.find(
            "select", {"id": "m_Content_TeacherMC_totalSet"})
        for user in teacher_select.find_all("option"):
            teacher_data = user.text.strip().split(" (")
            name = teacher_data[0]
            initials = teacher_data[1][:-1]
            self.teachers.append(
                User(self._lectio, int(user["value"][1:]), UserType.TEACHER, lazy=True, name=name, initials=initials))

        # Get school's rooms
        self.rooms = []
        room_select = soup.find(
            "select", {"id": "m_Content_RoomMC_totalSet"})
        for user in room_select.find_all("option"):
            self.rooms.append(Room(self._lectio, user["value"][2:], name))

    def get_user_by_id(self, user_id: str, user_type: UserType = None) -> User:
        """Gets a user by their id

        Args:
            user_id (str): The id of the user
            user_type (:class:`lectio.models.user.UserType`): The type of the user (student or teacher)

        Returns:
            :class:`lectio.models.user.User`: User object

        Raises:
            :class:`lectio.exceptions.UserDoesNotExistError`: When the user does not exist
        """

        if user_type == UserType.STUDENT or user_type is None:
            for student in self.students:
                if student.id == user_id:
                    return student

        if user_type == UserType.TEACHER or user_type is None:
            for teacher in self.teachers:
                if teacher.id == user_id:
                    return teacher

        raise exceptions.UserDoesNotExistError(
            f"User with id {user_id} does not exist")

    def search_for_teachers_by_name(self, query: str) -> Generator[User, None, None]:
        """Search for teachers by name or initials

        Args:
            query (str): Name to search for

        Yields:
            :class:`lectio.models.user.User`: Teacher object
        """

        for teacher in self.teachers:
            if query.lower() in teacher.name.lower():
                yield teacher

    def search_for_teachers_by_initials(self, query: str) -> Generator[User, None, None]:
        """Search for teachers by initials

        Args:
            query (str): Initials to search for

        Yields:
            :class:`lectio.models.user.User`: Teacher object
        """

        for teacher in self.teachers:
            if query.lower() in teacher.initials.lower():
                yield teacher

    def search_for_students(self, query: str) -> Generator[User, None, None]:
        """Search for user

        Args:
            query(str): Name to search for

        Yields:
            : class: `lectio.User`: User object
        """

        for student in self.students:
            if query.lower() in student.name.lower():
                yield student

    def search_for_users(self, query: str) -> Generator[User, None, None]:
        """Search for user

        Args:
            query(str): Name to search for

        Yields:
            : class: `lectio.models.user.User`: User object
        """

        yield from self.search_for_students(query)
        yield from self.search_for_teachers_by_name(query)

    def __repr__(self) -> str:
        return f"<School name={self.name}>"
