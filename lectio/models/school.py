from typing import TYPE_CHECKING, List
from bs4 import BeautifulSoup
import re
from urllib.parse import quote

from .user import User, UserType
from ..import exceptions

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

    def __init__(self, lectio: 'Lectio') -> None:
        self._lectio = lectio
        self.__populate()

    def __populate(self) -> None:
        r = self._lectio._request("forside.aspx")

        soup = BeautifulSoup(r.text, 'html.parser')

        self.name = soup.find(
            "div", {"id": "s_m_masterleftDiv"}).text.strip().split("\n")[0].replace("\r", "")

    def get_user_by_id(self, user_id: str, user_type: int = UserType.STUDENT, check: bool = True) -> User:
        """Gets a user by their id

        Args:
            user_id (str): The id of the user
            user_type (int): The type of the user (student or teacher)
            check (bool): Whether to check if the user exists (slower)

        Returns:
            :class:`lectio.models.user.User`: User object

        Raises:
            :class:`lectio.exceptions.UserDoesNotExistError`: When the user does not exist
        """

        if check:
            type_str = "elev" if user_type == UserType.STUDENT else "laerer"

            # Check if user exists
            r = self._request(
                f"SkemaNy.aspx?type={type_str}&{type_str}id={user_id}")

            soup = BeautifulSoup(r.text, 'html.parser')

            if soup.title.string.strip().startswith("Fejl - Lectio"):
                raise exceptions.UserDoesNotExistError(
                    f"The {UserType.get_str(user_type, True)} with the id '{user_id}' does not exist!")

        return User(self, user_id, user_type)

    def get_teachers(self) -> List[User]:
        """Get all teachers

        Returns:
            list(:class:`lectio.models.user.User`): List of teachers
        """

        r = self._lectio._request("FindSkema.aspx?type=laerer&sortering=id")

        soup = BeautifulSoup(r.text, 'html.parser')

        teachers = []

        # Container containing all teachers
        lst = soup.find("ul", {"class": "ls-columnlist mod-onechild"})

        if lst is None:
            return []

        # Iterate and create user objects
        for i in lst.find_all("li"):
            user_id = int(i.a["href"].split("=")[-1])

            user_name = i.a.contents[1].strip()

            initial_span = i.a.find('span')

            user_initials = None
            if initial_span is not None:
                user_initials = initial_span.text.strip()

            teachers.append(User(self._lectio,
                                 user_id,
                                 UserType.TEACHER,
                                 lazy=True,
                                 name=user_name,
                                 initials=user_initials))

        return teachers

    def search_for_teachers(self, query: str) -> List[User]:
        """Search for teachers

        Note:
            This method is not very reliable, and will sometimes return no results.
            Also, the query has to be from the beginning of the name.

            Example: Searching for "John" will return "John Doe", but searching for "Doe" will not.

        Args:
            query (str): Name to search for

        Returns:
            list(:class:`lectio.models.user.User`): List of teachers
        """

        res = []

        for teacher in self.get_teachers():
            if teacher.name.lower().startswith(query.lower()):
                res.append(teacher)

        return res

    def get_students_by_letter(self, letter: str) -> List[User]:
        """Get students by first letter of name

        Args:
            letter (str): Letter to search for

        Returns:
            list(:class:`lectio.models.user.User`): List of students
        """

        r = self._lectio._request(
            "FindSkema.aspx?type=elev&forbogstav=" + quote(letter.upper()))

        soup = BeautifulSoup(r.text, 'html.parser')

        students = []

        # Container containing all students
        lst = soup.find("ul", {"class": "ls-columnlist mod-onechild"})

        # Shouldn't happen in cases other than ``len(letter) > 1`` or if letter is not a valid character
        if lst is None:
            return []

        # Iterate and create user objects
        for i in lst.find_all("li"):
            user_id = int(i.a["href"].split("=")[-1])

            user_info = i.a.text.strip()

            # Search for name and class
            search = re.search(
                r"(?P<name>.*) \((?P<class_name>.*?) \d+?\)", user_info)

            if search is None:
                continue

            students.append(User(self._lectio,
                                 user_id,
                                 lazy=True,
                                 name=search.group("name"),
                                 class_name=search.group("class_name")))

        return students

    def search_for_students(self, query: str) -> List[User]:
        """Search for user

        Note:
            This method is not very reliable, and will sometimes return no results.
            Also, the query has to be from the beginning of the name.

            Example: Searching for "John" will return "John Doe", but searching for "Doe" will not.

        Args:
            query (str): Name to search for

        Returns:
            list(:class:`lectio.User`): List of users
        """

        res = []

        for student in self.get_students_by_letter(query[0]):
            if student.name.lower().startswith(query.lower()):
                res.append(student)

        return res

    def get_all_students(self) -> List[User]:
        """Get all students

        Returns:
            list(:class:`User`): List of students
        """

        res = []

        for letter in "abcdefghijklmnopqrstuvwxyzæøå":
            res.extend(self.get_students_by_letter(letter))

        return res

    def search_for_users(self, query: str) -> List[User]:
        """Search for user

        Args:
            query (str): Name to search for

        Returns:
            list(:class:`lectio.models.user.User`): List of users
        """

        return [*self.search_for_students(query), *self.search_for_teachers(query)]

    def __repr__(self) -> str:
        return f"School({self.name})"
