from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.db import models
from models import *

class LoginForm(AuthenticationForm):
    username = forms.CharField(label="Username", max_length=30,
                               widget=forms.TextInput(attrs={'class': 'form-control',
                                                             'name': 'username'}))
    password = forms.CharField(label="Password", max_length=30,
                               widget=forms.PasswordInput())


class ActivateAccountForm(forms.Form):
    activation_code = forms.CharField(label="Activation Code:", max_length=20)


class CreateAccountForm(forms.Form):
    email = forms.EmailField()
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
        if form_data['email'].split('@')[1]!="cs.uct.ac.za":
            self._errors["email"] = ["Email is not a valid UCT Computer Science department staff email address."]
            del form_data["email"]
        return form_data


class ProblemForm(forms.ModelForm):
    class Meta:
        model = Problem
        exclude = ('categories', 'forked_from',)


class CategoriesForm(forms.Form):
    categories = forms.CharField(max_length=1000)


class ChallengeForm(forms.ModelForm):
    class Meta:
        model = Challenge
        exclude = ('problems',)
