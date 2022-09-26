from typing import TYPE_CHECKING, List
from bs4 import BeautifulSoup

from .user import User

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

    def get_user_by_letter(self, letter: str) -> List[User]:
        """Get students by first letter of name

        Args:
            letter (str): Letter to search for

        Returns:
            list(:class:`lectio.User`): List of students
        """

        r = self._lectio._request("FindSkema.aspx?type=elev&forbogstav=" + letter)

        soup = BeautifulSoup(r.text, 'html.parser')

        students = []

        # Container containing all students
        lst = soup.find("ul", {"class": "ls-columnlist mod-onechild"})

        # Iterate and create user objects
        for i in lst.find_all("li"):
            students.append(User(self._lectio, int(i.a["href"].split("=")[-1])))

        return students

    def __repr__(self) -> str:
        return f"School({self.name})"
