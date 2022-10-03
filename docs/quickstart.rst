Quickstart
==========

Let's start with a simple example, where we will get your schedule for today.

Schedule
--------

First you need your institution id. To get your institution id, you can simply go to
your school's lectio login page, and look at the url. It should look something like this:

    https://www.lectio.dk/lectio/123/login.aspx

The number after lectio is your institution id. In this case it is ``123``.

Create a new file, and add the following code:

.. code-block:: python

    from lectio import Lectio
    from datetime import datetime, timedelta

    lec = Lectio(123, '<username>', '<password>')

    # Get my user object
    me = lec.me()

    # Get the schedule for today
    schedule = me.get_schedule(datetime.now(), datetime.now())

We now have a list of all :class:`lectio.models.module.Module` in the ``schedule`` variable. Let's print it:

.. code-block:: python

    for module in schedule:
        print(module.title, module.teacher, module.room)

**More to come...!**
