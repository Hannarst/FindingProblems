from django import forms
from models import *

class ProblemForm(forms.ModelForm):
    class Meta:
        model = Problem
        exclude = ('categories',)

class CategoriesForm(forms.Form):
    categories = forms.CharField(max_length=1000)
