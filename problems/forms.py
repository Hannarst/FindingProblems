from django import forms
from django.db import models
from models import *

class CreateAccountForm(forms.Form):
    email = models.EmailField()
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
        exclude = ('categories',)

class CategoriesForm(forms.Form):
    categories = forms.CharField(max_length=1000)


class ChallengeForm(forms.ModelForm):
    class Meta:
        model = Challenge
        exclude = ('problems',)
