from django import forms
from django.contrib.auth.forms import AuthenticationForm, PasswordResetForm
from django.db import models
from .models import *

class LoginForm(AuthenticationForm):
    """
    A form for handling the data for a user's login
    """
    username = forms.CharField(label="Username", max_length=30,
                               widget=forms.TextInput(attrs={'class': 'form-control',
                                                             'name': 'username'}))
    password = forms.CharField(label="Password", max_length=30,
                               widget=forms.PasswordInput())


class ActivateAccountForm(forms.Form):
    """
    A form for handling the data relating to a user's account activation
    """
    activation_code = forms.CharField(label="Activation Code:", max_length=20)


class CreateAccountForm(forms.Form):
    """A form for handling the data relating to creating a new account"""
    email = forms.EmailField(label="UCT Computer Science Department staff email address:", max_length=300,
                              widget=forms.EmailInput())
    password_one = forms.CharField(label="Password:", max_length=30,
                               widget=forms.PasswordInput())
    password_two = forms.CharField(label="Re-enter password:", max_length=30,
                                   widget=forms.PasswordInput())

    def clean(self):
        form_data = self.cleaned_data
        #passwords must match
        if form_data['password_one'] != form_data['password_two']:
            self._errors["password_one"] = ["Passwords do not match"] # Will raise a error message
            self._errors["password_two"] = ["Passwords do not match"]
            del form_data['password_one']
            del form_data['password_two']
        #email must be that of a uct cs department member
        if form_data['email'].split('@')[1]!="gmail.com":
            self._errors["email"] = ["Email is not a valid UCT Computer Science department staff email address."]
            del form_data["email"]
        return form_data


class ProblemForm(forms.ModelForm):
    """
    A form for handling the data surrounding creating, editing and forking an instance of a problem
    """
    class Meta:
        model = Problem
        exclude = ('created_by', 'content', 'solution', 'categories', 'forked_from',)


class ContentForm(forms.ModelForm):
    """
    A form for handling the data surrounding creating, editing and forking an instance of the content model
    """
    class Meta:
        model = Content
        fields = ('problem_description', 'example_input', 'example_output',)


class SolutionForm(forms.ModelForm):
    """
    A form for handling the data surrounding creating, editing and forking an instance of the solution model
    """
    class Meta:
        model = Solution
        fields = ('solution_description', 'links', 'example_code',  'time_limit', "solution_privacy",)


class PDFForm(forms.Form):
    """
    A form for handling the data surrounding creating a problem from a PDF
    """
    problem = forms.FileField(required=False)
    solution = forms.FileField(required=False)


class ChallengeForm(forms.ModelForm):
    """
    A form for handling the data surrounding creating, editing and forking an instance of the challenge model
    """
    class Meta:
        model = Challenge
        exclude = ('problems',)
