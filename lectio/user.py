from datetime import datetime, timedelta
from typing import TYPE_CHECKING, List

from bs4 import BeautifulSoup

from .helpers.schedule import get_sched_for_student

if TYPE_CHECKING:
    from .helpers.schedule import Module
    from .lectio import Lectio


class Types:
    STUDENT = 0
    TEACHER = 1


class UserMixin:
    name = None

    def __init__(self, lectio: 'Lectio', user_id: int):
        self._lectio = lectio
        self.user_id = user_id


class Student(UserMixin):
    def get_name(self):
        # TODO
        #return self._lectio._request("")

    def get_schedule(self, start_date: datetime, end_date: datetime, strip_time: bool = True) -> List['Module']:
        return get_sched_for_student(self._lectio, self.user_id, start_date, end_date, strip_time)

    def __repr__(self) -> str:
        return f"Student({self.user_id})"


class Teacher(UserMixin):
    def get_schedule(self, start_date: datetime, end_date: datetime, strip_time: bool = True) -> List['Module']:
        # TODO
        #get_sched_for_teacher(self._lectio, self.user_id, start_date, end_date, strip_time)
        pass

    def __repr__(self) -> str:
        return f"Teacher({self.user_id})"
