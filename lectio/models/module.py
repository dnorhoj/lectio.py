from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..lectio import Lectio
    from .user import User


class Module:
    """Lectio module object

    Represents a lectio module

    Args:
        title (str|None): Optional description of module (not present in all modules)
        subject (str|None): "Hold" from lectio, bascially which subject.
            Example: `1.a Da`
        teacher (str|None): Initials of teacher.
            Example: `abcd`
        room (str|None): Room name of module.
            Example: `0.015`
        extra_info (str|None): Extra info from module, includes homework and other info.
        start_time (:class:`datetime.datetime`): Start time of module
        end_time (:class:`datetime.datetime`): End time of module
        status (int): 0=normal, 1=changed, 2=cancelled
        url (str|None): Url for more info for the module
    """

    def __init__(self, lectio: 'Lectio', **kwargs) -> None:
        self._lectio = lectio

        self.title = kwargs.get("title")
        self.subject = kwargs.get("subject")
        self.teacher = kwargs.get("teacher")
        self.room = kwargs.get("room")
        self.extra_info = kwargs.get("extra_info")
        self.start_time = kwargs.get("start_time")
        self.end_time = kwargs.get("end_time")
        self.status = kwargs.get("status")
        self.url = kwargs.get("url")

    def get_homework(self) -> str:
        raise NotImplementedError("Not implemented yet")

    def get_teacher(self) -> 'User':
        """Get teacher

        Returns:
            lectio.models.user.User: Teacher object
        """

        return self._lectio.get_school().search_for_teachers_by_name(self.teacher)[0]

    def __repr__(self) -> str:
        return f"<Module subject={self.subject} start={self.start_time} end={self.end_time}>"
