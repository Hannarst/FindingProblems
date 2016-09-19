from __future__ import unicode_literals
from hashlib import md5
import random
import datetime
import markdown2

from django.core.exceptions import ValidationError
from django.db import models
from django.contrib.auth.models import User
from django.core.mail import send_mail

def get_html(content):
    return markdown2.markdown(content, extras=["fenced-code-blocks"])


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
    type_choices = zip(range(3), ("paradigm", "data-structure", "complexity", "algorithm", "language"))
    name = models.TextField(max_length=200)
    type = models.CharField(max_length=200, choices=type_choices, default="paradigm")

    class Meta:
        unique_together = ['name', 'type']


class Problem(models.Model):
    DIFFICULTIES = zip(range(5), ['Very Easy', 'Easy', 'Average', 'Difficult', 'Very Difficult'])
    created_by = models.ForeignKey(User)
    title = models.CharField(max_length=200)
    difficulty = models.IntegerField(default=0, choices=DIFFICULTIES)
    problem_privacy = models.BooleanField(default=True)
    categories = models.ManyToManyField(Category, blank=True, related_name="paradigms")
    forked_from = models.CharField(max_length=200,default="Original")

    class Meta:
        unique_together = ['title']


class Content(models.Model):
    problem = models.ForeignKey(Problem)
    problem_description = models.TextField()
    problem_description_html = models.TextField()
    example_input = models.TextField(default="No example input provided.")
    example_input_html = models.TextField()
    example_output = models.TextField(default="No example output provided.")
    example_output_html = models.TextField()

    def save(self, *args, **kwargs):
        self.problem_description_html = get_html(self.problem_description)
        self.example_input_html = get_html(self.example_input)
        self.example_output_html = get_html(self.example_output)
        super(Content, self).save(*args, **kwargs)


class Solution(models.Model):
    problem = models.ForeignKey(Problem)
    solution_privacy = models.BooleanField(default=True)
    solution_description = models.TextField(default="No solution description has been provided.")
    solution_description_html = models.TextField()
    complexity = models.ForeignKey(Category, null=True, blank=True, related_name="complexity")
    time_limit = models.FloatField(default=0)
    links = models.TextField(default="No links.")
    links_html = models.TextField()
    example_code = models.TextField(default="No example solution code.")
    example_code_html = models.TextField()
    language = models.ManyToManyField(Category, blank=True, related_name="language")
    data_structures = models.ManyToManyField(Category, blank=True, related_name="data_structures")
    algorithms = models.ManyToManyField(Category, blank=True, related_name="algorithms")

    def save(self, *args, **kwargs):
        self.solution_description_html = get_html(self.solution_description)
        self.links_html = get_html(self.links)
        self.example_code_html = get_html(self.example_code)
        super(Solution, self).save(*args, **kwargs)

    def all_defaults(self):
        return self.solution_description=="No solution description has been provided." and self.links=="No links." and self.example_code=="No example solution code."

    def get_all_categories(self):
        categories = []
        problem_categories = self.problem.categories.all()
        for c in problem_categories:
            categories.append(c)
        solution_ds = self.data_structures.all()
        for d in solution_ds:
            categories.append(d)
        solution_alg = self.algorithms.all()
        for a in solution_alg:
            categories.append(a)
        solution_c = self.complexity
        categories.append(solution_c)
        solution_lang = self.language.all()
        for l in solution_lang:
            categories.append(l)
        return categories


class Challenge(models.Model):
    name = models.CharField(max_length=200)
    date = models.DateField()
    time = models.TimeField(default=datetime.time(0))
    problems = models.ManyToManyField(Problem)
