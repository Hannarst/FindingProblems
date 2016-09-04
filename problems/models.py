from __future__ import unicode_literals
from _md5 import md5
import random
import datetime
from django.db import models
from django.contrib.auth.models import User
from django.core.mail import send_mail

class Account(models.Model):
    user = models.ForeignKey(User)
    activation_code = models.CharField(max_length=20)
    activation_deadline = models.DateField()

    def new_deadline(self):
        today = datetime.date.today()
        deadline = today + datetime.timedelta(days=7)
        return deadline

    def new_activation_code(self):
        random_float = random.random()
        _hash = md5(str(random_float)).hexdigest()
        activation_code = _hash[:20]
        return activation_code

    def reset_activation_code(self):
        self.activation_code = self.new_activation_code()
        self.activation_deadline = self.new_activation_deadline()
        self.save()
        send_mail(
            'Activation code for FindingProblems.com',
            'Please use the following code to activate your account when you first log into the website: '+str(self.activation_code),
            'findingproblemstest@gmail.com',
            [self.user.username],
            fail_silently=False,
        )


class Category(models.Model):
    name = models.TextField(max_length=200)


class Problem(models.Model):
    DIFFICULTIES = zip(range(5), ['Very Easy', 'Easy', 'Average', 'Difficult', 'Very Difficult'])
    title = models.TextField(max_length=200)
    content = models.TextField()
    difficulty = models.IntegerField(choices=DIFFICULTIES)
    execution_time_limit = models.FloatField()
    solution = models.TextField()
    private = models.BooleanField(default=True)
    categories = models.ManyToManyField(Category)
    forked_from = models.CharField(default="Original")


class Challenge(models.Model):
    date = models.DateField()
    time = models.TimeField()
    name = models.CharField(max_length=200)
    problems = models.ManyToManyField(Problem)
