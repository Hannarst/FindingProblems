from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.db import models
from .models import *

class LoginForm(AuthenticationForm):
    username = forms.CharField(label="Username", max_length=30,
                               widget=forms.TextInput(attrs={'class': 'form-control',
                                                             'name': 'username'}))
    password = forms.CharField(label="Password", max_length=30,
                               widget=forms.PasswordInput())


class ActivateAccountForm(forms.Form):
    activation_code = forms.CharField(label="Activation Code:", max_length=20)


class CreateAccountForm(forms.Form):
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


factorial = Category(name="O(n!)", type="complexity").save()
exponential = Category(name="O(2^n)", type="complexity").save()
squared = Category(name='O(n^2)', type="complexity").save()
n_log_n = Category(name='O(nlogn)', type="complexity").save()
n = Category(name='O(n)', type="complexity").save()
log_n = Category(name='O(logn)', type="complexity").save()
constant = Category(name='O(1)', type="complexity").save()

class SolutionForm(forms.ModelForm):
    class Meta:
        model = Solution
        fields = ('solution_description', 'links', 'example_code', 'language',)


class ContentForm(forms.ModelForm):
    class Meta:
        model = Content
        fields = ('problem_description', 'example_input', 'example_output',)


class ProblemForm(forms.ModelForm):
    class Meta:
        model = Problem
        exclude = ('content', 'solution', 'categories', 'forked_from',)


class CategoriesForm(forms.Form):
    categories = forms.CharField(max_length=1000)


class ChallengeForm(forms.ModelForm):
    class Meta:
        model = Challenge
        exclude = ('problems',)


class PDFForm(forms.Form):
    problem = forms.FileField()
    solution = forms.FileField()

    def clean(self):
        form_data = self.cleaned_data
        if form_data['problem'] == None:
            pass
        if form_data['solution'] == None:
            pass
        return form_data
