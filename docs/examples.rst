Examples
==========

On this page you can find some examples on how to use the lectio.py library.

Authentication
--------------

To authenticate you need three things:

* Your institution id
* Your username
* Your password

First you need your institution id. To get your institution id, you can simply go to
your school's lectio login page, and look at the url. It should look something like this:

    https://www.lectio.dk/lectio/123/login.aspx

The number after lectio is your institution id. (In this case ``123``)

We can now create a new :class:`lectio.Lectio` object by creating a new file and adding the following code:

.. code-block:: python

    from lectio import Lectio

    lec = Lectio(123, '<username>', '<password>')

Now we have a :class:`lectio.Lectio` object, which we can use to get information from lectio.

Get my user object
------------------

Your user object contains information about you, such as your name and your id.
It can also be used to fetch data such as your schedule, absences and more.

You can get your user object by calling the :meth:`lectio.Lectio.get_user` method:

.. code-block:: python

    from lectio import Lectio

    lec = Lectio(123, '<username>', '<password>')
    
    me = lec.get_user()

The ``me`` variable now contains your user object. We can for example print your name:

.. code-block:: python

    print(me.name)

Get my schedule
---------------

You can get your schedule by calling the :meth:`lectio.User.get_schedule` method with a start and end date:

.. code-block:: python

    from lectio import Lectio
    from datetime import datetime

    lec = Lectio(123, '<username>', '<password>')

    me = lec.get_user()

    schedule = me.get_schedule(datetime.now(), datetime.now())

The ``schedule`` variable now contains your schedule, which is a list of :class:`~lectio.models.module.Module` objects.

You might be wondering what the ``datetime.now()`` is. It is simply a date, and you can replace it with any date you want.
In this example we are getting the schedule for today.

We can now loop through the schedule and print the name of each module:

.. code-block:: python

    for module in schedule:
        print(module.name)

You can read more about the :class:`~lectio.models.module.Module` object by going to the reference.

**More to come...!**
