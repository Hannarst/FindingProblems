from __future__ import unicode_literals
from hashlib import md5
import random
import datetime

from django.core.exceptions import ValidationError
from django.db import models
from django.contrib.auth.models import User
from django.core.mail import send_mail

class Account(models.Model):
    user = models.ForeignKey(User)
    activation_code = models.CharField(max_length=20)
    activation_deadline = models.DateField()
    activated = models.BooleanField(default=False)

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


class Content(models.Model):
    description = models.TextField()
    example_input = models.TextField()
    example_output = models.TextField()
    examples = models.TextField()

    def clean(self):
        super(Content, self).clean()
        if self.description is None:
            raise ValidationError("Please provide a description of the problem.")
        else:
            if self.example_input is None:
                pass
            if self.example_output is None:
                pass
            if self.examples is None:
                pass

class Solution(models.Model):
    description = models.TextField()
    links = models.TextField()
    example_code = models.TextField()
    language = models.CharField(max_length=200, default=None)

    def clean(self):
        super(Solution, self).clean()

        if self.description is None:
            if self.links and self.example_code is None:
                raise ValidationError("Please provide at least one of the following: a description of the solution, links to explanations of the solution or a coded sample solution.")
        if self.links is None:
            if self.description and self.example_code is None:
                raise ValidationError("Please provide at least one of the following: a description of the solution, links to explanations of the solution or a coded sample solution.")
        if self.example_code is None:
            if self.links and self.description is None:
                raise ValidationError("Please provide at least one of the following: a description of the solution, links to explanations of the solution or a coded sample solution.")
            if self.language:
                raise ValidationError("Please provide a coded example in this language.")
        if self.language is None:
            if self.example_code:
                raise ValidationError("Please provide the language in which the example solution has been coded.")


class Problem(models.Model):
    DIFFICULTIES = zip(range(5), ['Very Easy', 'Easy', 'Average', 'Difficult', 'Very Difficult'])
    RUNTIMES = zip(range(7), ['O(n!)', 'O(2^n)', 'O(n^2)', 'O(nlogn)', 'O(n)', 'O(logn)', 'O(1)'])
    title = models.CharField(max_length=200)
    content = models.ForeignKey(Content)
    difficulty = models.IntegerField(default=0, choices=DIFFICULTIES)
    complexity = models.IntegerField(default=0, choices=RUNTIMES)
    solution = models.ForeignKey(Solution)
    private = models.BooleanField(default=True)
    categories = models.ManyToManyField(Category)
    forked_from = models.CharField(max_length=200,default="Original")

    class Meta:
        unique_together = ['title']


class Challenge(models.Model):
    date = models.DateField()
    time = models.TimeField()
    name = models.CharField(max_length=200)
    problems = models.ManyToManyField(Problem)
