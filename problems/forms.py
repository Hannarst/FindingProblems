from django.forms import ModelForm
from models import *

class ProblemForm(ModelForm):
    class Meta:
        model = Problem
        fields = '__all__'

class EditProblemForm(ModelForm):
    class Meta:
	model = Problem
	fields = '__all__'
