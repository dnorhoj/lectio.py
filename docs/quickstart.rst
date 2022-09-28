Quickstart
==========

Let's start with a simple example, where we will get your schedule for today.

Schedule
--------

Create a new file, and add the following code:

.. code-block:: python

    from lectio import Lectio
    from datetime import datetime, timedelta

    lec = Lectio('<username>', '<password>')

    # Get my user object
    me = lec.me()

    # Get the schedule for today
    schedule = me.get_schedule(datetime.now(), datetime.now() + timedelta(days=1))

We now have a list of all :class:`lectio.helpers.Module` in the ``schedule`` variable. Let's print it:

.. code-block:: python

    for module in schedule:
        print(module.title, module.teacher, module.room)

**More to come...!**
