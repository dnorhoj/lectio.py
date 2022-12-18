from typing import List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from ..lectio import Lectio
    from ..models import Room
    from .user import User
    import datetime
    from ..helpers import ModuleStatus


class Module:
    """Lectio module object

    Represents a lectio module
    """

    #: Description of module
    title: Optional[str]
    #: "Hold" from lectio, bascially which subject.
    subject: Optional[str]
    #: Initials of teacher.
    teacher: Optional[str]
    #: Room name of module.
    room: Optional[str]
    #: Extra info from module, includes homework and other info.
    extra_info: Optional[str]
    #: Start time of module
    start_time: 'datetime.datetime'
    #: End time of module
    end_time: 'datetime.datetime'
    #: Module status
    status: 'ModuleStatus'
    #: Url for more info for the module
    url: Optional[str]

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

    def get_extra_info(self) -> str:
        raise NotImplementedError("Not implemented yet")

    def get_teachers(self) -> List['User']:
        """Get teachers

        Returns:
            List[User]: List of teacher user objects
        """

        raise NotImplementedError("Not implemented yet")

    def get_rooms(self) -> List['Room']:
        """Get rooms

        Returns:
            List[Room]: Room object
        """

        raise NotImplementedError("Not implemented yet")

    def get_team(self) -> None:
        """Get team

        Returns:
            TODO: Team name
        """

        raise NotImplementedError("Not implemented yet")

    def __repr__(self) -> str:
        return f"<Module subject={self.subject} start={self.start_time} end={self.end_time}>"
