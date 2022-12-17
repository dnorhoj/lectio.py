from dataclasses import dataclass
import re
from bs4 import BeautifulSoup
from typing import TYPE_CHECKING, List, Tuple, Union
import json

if TYPE_CHECKING:
    from ..lectio import Lectio


class Absence:
    """Class for representing a user's absences

    Note:
        This class should not be instantiated directly,
        but rather through the :attr:`lectio.models.user.Me.absences` method

    Attributes:
        absences (List[SubjectAbsenceData]): List of absence data for each subject
    """

    subjects: List['SubjectAbsenceData']
    total_absences: 'AbsenceData'

    def __init__(self, lectio: 'Lectio') -> None:
        self._lectio = lectio

        self._populate()

    def _populate(self) -> None:
        r = self._lectio._request(
            f"subnav/fravaerelev.aspx?elevid={self._lectio.me().id}")

        soup = BeautifulSoup(r.text, 'html.parser')

        table = soup.find(
            "table", {"id": "s_m_Content_Content_SFTabStudentAbsenceDataTable"})

        self.subjects = []

        for row in table.find_all("tr")[3:-1]:
            cols = row.find_all("td")

            # Subject and group id
            el = cols[0].find("a")
            subject = el.text
            group_id = re.search(r"holdelementid=(\d+)",
                                 el.attrs.get("href"))[1]

            # Physical
            calculated_physical = _parse_multiple_absence_percentage(
                [cols[1].text, cols[2].text])
            physical = _parse_multiple_absence_percentage(
                [cols[3].text, cols[4].text])

            # Assignment
            calculated_assignment = _parse_multiple_absence_percentage(
                [cols[5].text, cols[6].text])
            assignment = _parse_multiple_absence_percentage(
                [cols[7].text, cols[8].text])

            absence_data = AbsenceData(
                physical_total=physical[0],
                physical_absent=physical[1],
                physical_percentage=physical[2],
                physical_calculated_total=calculated_physical[0],
                physical_calculated_absent=calculated_physical[1],
                physical_calculated_percentage=calculated_physical[2],
                assignment_total=assignment[0],
                assignment_absent=assignment[1],
                assignment_percentage=assignment[2],
                assignment_calculated_total=calculated_assignment[0],
                assignment_calculated_absent=calculated_assignment[1],
                assignment_calculated_percentage=calculated_assignment[2],
            )

            self.subjects.append(SubjectAbsenceData(
                subject=subject,
                group_id=group_id,
                absence_data=absence_data
            ))

        # Get total data
        cols = table.find_all("tr")[-1].find_all("td")

        # Physical
        calculated_physical = _parse_multiple_absence_percentage(
            [cols[1].find("b").text, cols[2].find("b").text])
        physical = _parse_multiple_absence_percentage(
            [cols[3].find("b").text, cols[4].find("b").text])

        # Assignment
        calculated_assignment = _parse_multiple_absence_percentage(
            [cols[5].find("b").text, cols[6].find("b").text])
        assignment = _parse_multiple_absence_percentage(
            [cols[7].find("b").text, cols[8].find("b").text])

        self.total_absences = AbsenceData(
            physical_total=physical[0],
            physical_absent=physical[1],
            physical_percentage=physical[2],
            physical_calculated_total=calculated_physical[0],
            physical_calculated_absent=calculated_physical[1],
            physical_calculated_percentage=calculated_physical[2],
            assignment_total=assignment[0],
            assignment_absent=assignment[1],
            assignment_percentage=assignment[2],
            assignment_calculated_total=calculated_assignment[0],
            assignment_calculated_absent=calculated_assignment[1],
            assignment_calculated_percentage=calculated_assignment[2],
        )

    def toJSON(self) -> str:
        """Return a JSON representation of all the absence data

        Returns:
            str: JSON representation of all the absence data in the following format:

                {
                    "subjects": [...],
                    "total": {...}
                }
        """

        return json.dumps({
            "subjects": self.subjects,
            "total": self.total_absences
        }, default=lambda o: o.__dict__)


def _parse_multiple_absence_percentage(cols: List[str]) -> Union[Tuple[int, int, float], Tuple[None, None, None]]:
    """Parse multiple absence percentage

    Args:
        cols (List[str]): List of string columns

    Returns:
        Union[Tuple[int, int, float], Tuple[None, None, None]]: Tuple of total, absence and percentage
    """

    percentage = cols[0]
    if "%" not in percentage:
        return None, None, None

    percentage = float(percentage[: -1].replace(",", "."))

    absence = float(cols[1].split("/")[0].replace(",", "."))
    total = float(cols[1].split("/")[1].replace(",", "."))

    return total, absence, percentage


@dataclass
class AbsenceData:
    """Class for representing a subject absence

    Attributes:
        physical_total (int): Total physical absence
        physical_absent (int): Physical absence
        physical_percentage (float): Physical absence percentage
        physical_calculated_total (int): Calculated total physical absence
        physical_calculated_absent (int): Calculated physical absence
        physical_calculated_percentage (float): Calculated physical absence percentage
        assignment_total (int): Total assignment absence
        assignment_absent (int): Assignment absence
        assignment_percentage (float): Assignment absence percentage
        assignment_calculated_total (int): Calculated total assignment absence
        assignment_calculated_absent (int): Calculated assignment absence
        assignment_calculated_percentage (float): Calculated assignment absence percentage
    """

    # Physical absence
    physical_total: int
    physical_absent: int
    physical_percentage: float

    physical_calculated_total: int
    physical_calculated_absent: int
    physical_calculated_percentage: float

    # Assignment absence
    assignment_total: int
    assignment_absent: int
    assignment_percentage: float

    assignment_calculated_total: int
    assignment_calculated_absent: int
    assignment_calculated_percentage: float

    def __iter__(self):
        return iter(self.__dict__.values())


@dataclass
class SubjectAbsenceData():
    """Class for representing a subject absence

    Attributes:
        subject (str): Subject name
        group_id (int): Group id
        absence_data (AbsenceData): Absence data
    """

    subject: str
    group_id: int
    absence_data: AbsenceData

    @property
    def group(self) -> None:
        """TODO: Return group object"""
        raise NotImplementedError("Not implemented yet")
