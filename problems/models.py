from __future__ import unicode_literals
from django.forms import ModelForm
from django.db import models

class Problem(models.Model):
    DIFFICULTIES = zip(range(5), ['Very Easy', 'Easy', 'Average', 'Difficult', 'Very Difficult'])
    title = models.TextField(max_length=200)
    content = models.TextField()
    difficulty = models.IntegerField(choices=DIFFICULTIES)
    execution_time_limit = models.FloatField()
    solution = models.TextField()
    private = models.BooleanField(default=True)

class Challenge(models.Model):
    datetime = models.DateTimeField()
    name = models.TextField(max_length=200)
    problems = models.ManyToManyField(Problem)

class Category(models.Model):
    problems = models.ManyToManyField(Problem)
    name = models.TextField(max_length=200)

class ProblemForm(ModelForm):
    class Meta:
        model = Problem
        fields = '__all__'
