Project: Finding Problems
===========================

A system for tracking competition problems, solutions, and the events in which they are used
The setting.py file expects a settings_secret.py file, which contains the secret key. As the name implies, it is secret. If you need it , please contact the developers.

Original Authors: Anna Borysova, Erin Versfeld, Qamran Tabo (August 2016)

Installation:
---------------------------------------

Set up a Virtualenv if required:

```
$ virtualenv venv
$ source venv/bin/activate
```

Run the below from the FindingProblems directory:

```
$ pip install Django
$ pip install django-bootstrap3
$ pip install markdown2
$ pip install reportlab
$ python manage.py makemigrations
$ python manage.py migrate
$ python manage.py populate
$ python manage.py runserver
```

