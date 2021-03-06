from __future__ import unicode_literals
from hashlib import md5
import random
import datetime
import markdown2

from django.core.exceptions import ValidationError
from django.db import models
from django.contrib.auth.models import User
from django.core.mail import send_mail

class Account(models.Model):
    """
    A model representing the account for a user
    """
    user = models.ForeignKey(User)
    activation_code = models.CharField(max_length=20)
    activation_deadline = models.DateField()
    activated = models.BooleanField(default=False)

    def new_deadline(self):
        """
        A helper function to generate a new deadline once the current one has passed
        :return: A datetime.date object
        """
        today = datetime.date.today()
        deadline = today + datetime.timedelta(days=7)
        return deadline

    def new_activation_code(self):
        """
        A helper function to generate a new activation code once the current one has expired
        :return: An alpha-numeric String object made up of 20 characters
        """
        random_float = random.random()
        _hash = md5(str(random_float)).hexdigest()
        activation_code = _hash[:20]
        return activation_code

    def reset_activation_code(self):
        """
        Reset the activation code for a user if an activation attempt occurs once the deadline has passed
        :return: An email to the user with the new activation code
        """
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
    """
    A model representing a possible categorisation of a problem or solution
    """
    type_choices = zip(range(3), ("paradigm", "data-structure", "complexity", "algorithm", "language"))
    name = models.TextField(max_length=200)
    type = models.CharField(max_length=200, choices=type_choices, default="paradigm")

    class Meta:
        unique_together = ['name', 'type']


class Problem(models.Model):
    """
    A model storing the data necessary to describe a problem
    """
    DIFFICULTIES = zip(range(5), ['Very Easy', 'Easy', 'Average', 'Difficult', 'Very Difficult'])
    created_by = models.ForeignKey(User)
    title = models.CharField(max_length=200)
    difficulty = models.IntegerField(default=0, choices=DIFFICULTIES)
    problem_privacy = models.BooleanField(default=True, verbose_name="Private (problem)")
    categories = models.ManyToManyField(Category, blank=True, related_name="paradigms")
    forked_from = models.CharField(max_length=200,default="Original")

    class Meta:
        unique_together = ['title']

    def add_paradigms(self, paradigms):
        """
        A helper function for adding new paradigms to the categories field
        :param paradigms: A string representing the paradigms which should be on the field
        :return: The saved object
        """
        if self.categories:
            self.remove_paradigms()
        for p in paradigms.split(','):
            if p == '' or p == ' ':
                pass
            else:
                paradigm, c = Category.objects.get_or_create(name=p.strip().lower(), type="paradigm")
                self.categories.add(paradigm)
        self.save()


    def remove_paradigms(self):
        """
        A helper function to remove paradigms from the categories field
        :return: The saved object
        """
        paradigms = self.categories.all()
        for p in paradigms:
            self.categories.remove(p)
        self.save()


class Content(models.Model):
    """
    A model storing the data necessary to describe the contents of a problem
    """
    problem = models.ForeignKey(Problem)
    problem_description = models.TextField()
    problem_description_html = models.TextField()
    example_input = models.TextField(default="No example input provided.")
    example_input_html = models.TextField()
    example_output = models.TextField(default="No example output provided.")
    example_output_html = models.TextField()

    def save(self, *args, **kwargs):
        """
        An extension to the default save method. This one updated the _html fields before writing the object to the
        database.
        :return: The saved object
        """
        self.problem_description_html = self.get_html(self.problem_description)
        self.example_input_html = self.get_html(self.example_input)
        self.example_output_html = self.get_html(self.example_output)
        super(Content, self).save(*args, **kwargs)

    def get_html(self, content):
        """
        A helper method for saving markdown formatted strings in HTML friendly formatting
        :param content: A string with markdown formatting
        :return: An HTML friendly version of the original string
        """
        return markdown2.markdown(content, extras=["fenced-code-blocks"])


class Solution(models.Model):
    """
    A model storing all of the data necessary to create a solution to a problem
    """
    problem = models.ForeignKey(Problem)
    solution_privacy = models.BooleanField(default=True, verbose_name="Private (solution)")
    solution_description = models.TextField(default="No solution description has been provided.")
    solution_description_html = models.TextField()
    complexity = models.ManyToManyField(Category, blank=True, related_name="complexity")
    time_limit = models.FloatField(default=0)
    links = models.TextField(default="No links.")
    links_html = models.TextField()
    example_code = models.TextField(default="No example solution code.")
    example_code_html = models.TextField()
    language = models.ManyToManyField(Category, blank=True, related_name="language")
    data_structures = models.ManyToManyField(Category, blank=True, related_name="data_structures")
    algorithms = models.ManyToManyField(Category, blank=True, related_name="algorithms")

    def save(self, *args, **kwargs):
        """
        An extension to the default save method. This one updated the _html fields before writing the object to the
        database.
        :return: The saved object
        """
        self.solution_description_html = self.get_html(self.solution_description)
        self.links_html = self.get_html(self.links)
        self.example_code_html = self.get_html(self.example_code)
        super(Solution, self).save(*args, **kwargs)

    def get_html(self, content):
        """
        A helper method for saving markdown formatted strings in HTML friendly formatting
        :param content: A string with markdown formatting
        :return: An HTML friendly version of the original string
        """
        return markdown2.markdown(content, extras=["fenced-code-blocks"])

    def add_complexity(self, complexities):
        """
        A helper function for adding new complexities to the complexity field
        :param paradigms: A string representing the complexities which should be on the field
        :return: The saved object
        """
        if self.complexity:
            self.remove_complexity()
        for complexity in complexities.split(','):
            if complexity == '' or complexity == ' ':
                pass
            else:
                complex, c = Category.objects.get_or_create(name=complexity.strip().lower(), type="complexity")
                self.complexity.add(complex)
        self.save()

    def remove_complexity(self):
        """
        A helper function to remove complexities from the complexity field
        :return: The saved object
        """
        complexity = self.complexity.all()
        for c in complexity:
            self.complexity.remove(c)
            self.save()

    def add_language(self, langs):
        """
        A helper function for adding new languages to the language field
        :param paradigms: A string representing the languages which should be on the field
        :return: The saved object
        """
        if self.language:
            self.remove_languages()
        for lang in langs.split(','):
            if lang == '' or lang == ' ':
                pass
            else:
                language, l = Category.objects.get_or_create(name=lang.strip().lower(), type="language")
                self.language.add(language)
        self.save()

    def remove_languages(self):
        """
        A helper function to remove languages from the language field
        :return: The saved object
        """
        languages = self.language.all()
        for l in languages:
            self.language.remove(l)
        self.save()

    def add_algorithms(self, algorithms):
        """
        A helper function for adding new algorithms to the algorithms field
        :param paradigms: A string representing the algorithms which should be on the field
        :return: The saved object
        """
        if self.algorithms:
            self.remove_algorithms()
        for a in algorithms.split(','):
            if a == '' or a == ' ':
                pass
            else:
                algorithm, a = Category.objects.get_or_create(name=a.strip().lower(), type="algorithm")
                self.algorithms.add(algorithm)
        self.save()

    def remove_algorithms(self):
        """
        A helper function to remove algorithms from the algorithms field
        :return: The saved object
        """
        algorithms = self.algorithms.all()
        for a in algorithms:
            self.algorithms.remove(a)
        self.save()

    def add_ds(self, data_structures):
        """
        A helper function for adding new data structures to the data_structures field
        :param paradigms: A string representing the data structures which should be on the field
        :return: The saved object
        """
        if self.data_structures:
            self.remove_ds()
        for ds in data_structures.split(','):
            if ds == '' or ds == ' ':
                pass
            else:
                data_structure, d = Category.objects.get_or_create(name=ds.strip().lower(), type="data-structure")
                self.data_structures.add(data_structure)
        self.save()

    def remove_ds(self):
        """
        A helper function to remove data structures from the data_structures field
        :return: The saved object
        """
        ds = self.data_structures.all()
        for d in ds:
            self.data_structures.remove(d)
        self.save()

    def all_defaults(self):
        """
        A helper method for determining if the user has supplied any details to the solution model
        :return: True if the user has made no changes to the default values for the model, otherwise False
        """
        default_categories = self.language.count()==0 and self.data_structures.count()==0 and self.algorithms.count()==0 and self.complexity.count()==0
        default_string = self.solution_description=="No solution description has been provided." and self.links=="No links." and self.example_code=="No example solution code."
        return default_categories and default_string and self.time_limit==0.0

    def get_all_categories(self):
        """
        A helper method for getting the complete categorisation of a solution and its corresponding problem
        :return: A list of the names of all the categories to which the solution and problem belong
        """
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
        solution_c = self.complexity.all()
        for c in solution_c:
            categories.append(c)
        solution_lang = self.language.all()
        for l in solution_lang:
            categories.append(l)
        return categories


class Challenge(models.Model):
    """
    A model storing all of the data necessary to manage a challenge
    """
    name = models.CharField(max_length=200)
    date = models.DateField()
    time = models.TimeField(default=datetime.time(0))
    problems = models.ManyToManyField(Problem)
