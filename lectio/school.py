from typing import TYPE_CHECKING, List
from bs4 import BeautifulSoup
import re

from .user import User, UserType

if TYPE_CHECKING:
    from .lectio import Lectio


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

    def get_user_by_letter(self, letter: str, user_type: int = UserType.STUDENT) -> List[User]:
        """Get students by first letter of name

        Args:
            letter (str): Letter to search for

        Returns:
            list(:class:`lectio.User`): List of students

        Raises:
            NotImplementedError: If user_type is UserType.TEACHER, as this is not implemented
        """

        if user_type == UserType.TEACHER:
            raise NotImplementedError(
                "Getting teachers by letter is not implemented")  # TODO

        r = self._lectio._request(
            "FindSkema.aspx?type=elev&forbogstav=" + letter.upper())

        soup = BeautifulSoup(r.text, 'html.parser')

        students = []

        # Container containing all students
        lst = soup.find("ul", {"class": "ls-columnlist mod-onechild"})

        # Shouldn't happen in cases other than `len(letter) > 1` or if letter is not a valid character
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

    def search_for_user(self, query: str, user_type: int = UserType.STUDENT) -> List[User]:
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
        for student in self.get_user_by_letter(query[0], user_type):
            if student.name.lower().startswith(query.lower()):
                res.append(student)

        return res

    def get_all_users(self, user_type: int = UserType.STUDENT) -> List[User]:
        """Get all users

        Args:
            user_type (int): The type of the user (student or teacher)

        Returns:
            list(:class:`lectio.User`): List of users
        """

        res = []
        for letter in "abcdefghijklmnopqrstuvwxyzæøå":
            res.extend(self.get_user_by_letter(letter))

        return res

    def __repr__(self) -> str:
        return f"School({self.name})"
