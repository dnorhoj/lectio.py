from typing import TYPE_CHECKING, List
from datetime import datetime, timedelta

from ..helpers.schedule import ModuleStatus
from ..helpers.schedule import get_schedule

if TYPE_CHECKING:
    from ..lectio import Lectio
    from .module import Module


class Room:
    """A room object.

    Represents a room.

    Note:
        This class should not be instantiated directly,
        but rather through the :meth:`lectio.Lectio.get_room` method.

    Args:
        lectio (Lectio): Lectio object
        id (int): Room id
        name (str): Room name
    """

    def __init__(self, lectio: 'Lectio', room_id: int, name: str) -> None:
        self._lectio = lectio
        self.id = room_id
        self.name = name

    def get_schedule(self, start_date: datetime, end_date: datetime, strip_time: bool) -> List['Module']:
        """Get schedule for room

        Note:
            As lectio is weird, you can only get a schedule for a range
            that is less than one month.
            If you specify a range greater than one month, you will get an empty return list.

        Args:
            start_date (:class:`datetime.datetime`): Start date
            end_date (:class:`datetime.datetime`): End date
            strip_time (bool): Whether to remove hours, minutes and seconds from date info, also adds 1 day to end time.
                Basically just allows you to put in a random time of two days, and still get all modules from all the days including start and end date.

        Returns:
            List[Module]: List of modules
        """

        return get_schedule(
            self._lectio,
            [f"lokalesel={self.id}"],
            start_date,
            end_date,
            strip_time
        )

    def is_available(self, date: datetime = None) -> bool:
        """Check if room is available at a given time

        Args:
            datetime (:class:`datetime.datetime`): Datetime to check (defaults to now)
        """

        if date is None:
            date = datetime.now()

        sched = self.get_schedule(date, date + timedelta(seconds=1), False)

        return len(sched) == 0 or all(map(lambda x: x.status == ModuleStatus.CANCELLED, sched))

    def __repr__(self) -> str:
        return f"<Room name={self.name} id={self.id}>"
