from datetime import datetime
from typing import TYPE_CHECKING, List
from bs4 import BeautifulSoup

if TYPE_CHECKING:
    from ..lectio import Lectio


class Assignment:
    """Lectio assignment object

    Represents a lectio assignment

    Args:
        week (int|None): Week number of the deadline.
            Example: `12`
        subject (str|None): "Hold" from lectio, bascially which subject.
            Example: `1.a Da`
        title (str|None): Title of the assignment
        deadline (:class:`datetime.datetime`|None): Deadline of the assignment
        student_time (float|None): Expected student time in hours ("Elevtid")
        status (str|None): Status of the assignment.
            Example: `Afleveret`, `Mangler` or `Venter`
        absence (str|None): Absence registered on the assignment.
            Example: `0%`
        waiting_for (str|None): Who the assignment is waiting for ("Afventer").
            Example: `Elev` or `Lærer`
        note (str|None): Assignment note ("Opgavenote")
        grade (str|None): Grade given for the assignment
        student_note (str|None): Student note ("Elevnote")
        url (str|None): Url for more info for the assignment
    """

    def __init__(self, **kwargs) -> None:
        self.week = kwargs.get("week")
        self.subject = kwargs.get("subject")
        self.title = kwargs.get("title")
        self.deadline = kwargs.get("deadline")
        self.student_time = kwargs.get("student_time")
        self.status = kwargs.get("status")
        self.absence = kwargs.get("absence")
        self.waiting_for = kwargs.get("waiting_for")
        self.note = kwargs.get("note")
        self.grade = kwargs.get("grade")
        self.student_note = kwargs.get("student_note")
        self.url = kwargs.get("url")

    def __repr__(self) -> str:
        return f"Assignment({self.subject}, {self.title}, {self.deadline})"

    def display(self):
        print(f"Title:        {self.title}")
        print(f"Subject:      {self.subject}")
        print(f"Week:         {self.week}")
        print(f"Deadline:     {self.deadline}")
        print(f"Student time: {self.student_time}")
        print(f"Status:       {self.status}")
        print(f"Absence:      {self.absence}")
        print(f"Waiting for:  {self.waiting_for}")
        print(f"Grade:        {self.grade}")
        print(f"URL:          {self.url}")
        print(f"Note:\n\n{self.note}")
        print(f"Student note:\n\n{self.student_note}")


# Maps lectio table headers to Assignment attributes
HEADERS = {
    "Uge": "week",
    "Hold": "subject",
    "Opgavetitel": "title",
    "Frist": "deadline",
    "Elevtid": "student_time",
    "Status": "status",
    "Fravær": "absence",
    "Afventer": "waiting_for",
    "Opgavenote": "note",
    "Karakter": "grade",
    "Elevnote": "student_note",
}


def get_assignments(lectio: 'Lectio', student_id: int) -> List[Assignment]:
    """Get all assignments for a student.

    Parameters:
        lectio (:class:`lectio.Lectio`): Base lectio object
        student_id (int): Id of the student

    Returns:
        List[:class:`lectio.helpers.assignments.Assignment`]: List containing all assignments.
    """

    assignments_request = lectio._request(
        f"OpgaverElev.aspx?elevid={student_id}")

    soup = BeautifulSoup(assignments_request.text, 'html.parser')

    assignment_table = soup.find(
        "table", {"id": "s_m_Content_Content_ExerciseGV"})

    if not assignment_table:
        return []

    rows = assignment_table.find_all("tr")

    if not rows:
        return []

    # Find attribute name of each column, so column order doesn't matter
    columns = [HEADERS.get(th.text.strip())
               for th in rows[0].find_all("th")]

    assignments = []
    for row in rows[1:]:
        cells = row.find_all("td")

        if len(cells) != len(columns):
            continue

        assignment = parse_assignment_row(columns, cells)

        # Add href to assignment
        a = row.find("a")
        if a and a.attrs.get("href"):
            assignment.url = f"https://www.lectio.dk{a.attrs.get('href')}"

        assignments.append(assignment)

    return assignments


def parse_assignment_row(columns: List[str], cells: list) -> Assignment:
    assignment = Assignment()

    for column, cell in zip(columns, cells):
        if column is None:
            continue

        value = cell.get_text("\n").strip() or None

        setattr(assignment, column, value)

    # Parse week
    if assignment.week and assignment.week.isdigit():
        assignment.week = int(assignment.week)

    # Parse deadline
    if assignment.deadline:
        try:
            assignment.deadline = datetime.strptime(
                assignment.deadline, "%d/%m-%Y %H:%M")
        except ValueError:
            pass

    # Parse student time
    if assignment.student_time:
        try:
            assignment.student_time = float(
                assignment.student_time.replace(",", "."))
        except ValueError:
            pass

    return assignment
