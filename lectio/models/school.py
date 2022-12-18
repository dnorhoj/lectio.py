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

    Example:
        .. code-block:: python

            import lectio

            lectio = lectio.Lectio(123, "username", "password")

            school = lectio.get_school()

            print(school.name)
    """

    #: List of students in the school
    students: List[User]

    #: List of teachers in the school
    teachers: List[User]

    #: List of groups in the school (TODO
    groups: List[None]

    #: List of rooms in the school
    rooms: List[Room]

    #: Name of the school
    name: str

    def __init__(self, lectio: 'Lectio') -> None:
        self._lectio = lectio
        self.__populate()

    def __populate(self) -> None:
        # In the advanced schedule finder, we get all users, rooms and groups
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
                User(self._lectio, int(user["value"][1:]), UserType.STUDENT, name))

        # Get school's teachers
        self.teachers = []
        teacher_select = soup.find(
            "select", {"id": "m_Content_TeacherMC_totalSet"})
        for user in teacher_select.find_all("option"):
            teacher_data = user.text.strip().split(" (")
            name = teacher_data[0]
            initials = teacher_data[1][:-1]
            self.teachers.append(
                User(self._lectio, int(user["value"][1:]), UserType.TEACHER, name, initials=initials))

        # Get school's rooms
        self.rooms = []
        room_select = soup.find(
            "select", {"id": "m_Content_RoomMC_totalSet"})
        for room in room_select.find_all("option"):
            self.rooms.append(
                Room(self._lectio, int(room["value"][2:]), room.text.strip()))

    def get_user_by_id(self, user_id: int, user_type: UserType = None, lazy=False) -> User:
        """Gets a user by their id

        Args:
            user_id (int): The id of the user
            user_type (:class:`~lectio.models.user.UserType`): The type of the user (student or teacher)
            lazy (bool): Whether to return a lazy user object or not (default: False)

        Returns:
            User: User object

        Raises:
            exceptions.UserDoesNotExistError: When the user does not exist
        """

        user_id = int(user_id)

        if user_type == UserType.STUDENT or user_type is None:
            for student in self.students:
                if student.id == user_id:
                    # Populate user if not lazy
                    if not lazy:
                        student.populate()
                    return student

        if user_type == UserType.TEACHER or user_type is None:
            for teacher in self.teachers:
                if teacher.id == user_id:
                    # Populate user if not lazy
                    if not lazy:
                        teacher.populate()
                    return teacher

        return User(self._lectio, user_id, user_type=user_type, lazy=lazy)

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
            User: Teacher user object
        """

        for teacher in self.teachers:
            if query.lower() in teacher.initials.lower():
                yield teacher

    def search_for_students(self, query: str) -> Generator[User, None, None]:
        """Search for user

        Args:
            query(str): Name to search for

        Yields:
            User: Student user object
        """

        for student in self.students:
            if query.lower() in student.name.lower():
                yield student

    def search_for_users(self, query: str) -> Generator[User, None, None]:
        """Search for user

        Args:
            query(str): Name to search for

        Yields:
            User: User object
        """

        yield from self.search_for_students(query)
        yield from self.search_for_teachers_by_name(query)

    def get_room_by_id(self, room_id: int) -> Room:
        """Gets a room by its id

        Args:
            room_id (int): The id of the room

        Returns:
            Room: Room object

        Raises:
            exceptions.RoomDoesNotExistError: When the room does not exist
        """

        room_id = int(room_id)

        for room in self.rooms:
            if room.id == room_id:
                return room

        raise exceptions.RoomDoesNotExistError(
            f"Room with id {room_id} does not exist")

    def search_for_rooms(self, query: str) -> Generator[Room, None, None]:
        """Search for room

        Args:
            query(str): Name to search for

        Yields:
            Room: Room object
        """

        for room in self.rooms:
            if query.lower() in room.name.lower():
                yield room

    def __repr__(self) -> str:
        return f"<School name={self.name}>"
