from __future__ import unicode_literals
from django.db import models

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

class Challenge(models.Model):
    date = models.DateField()
    time = models.TimeField()
    name = models.CharField(max_length=200)
    problems = models.ManyToManyField(Problem)
