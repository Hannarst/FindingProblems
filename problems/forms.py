from django.forms import ModelForm

class ProblemForm(ModelForm):
    class Meta:
        model = Problem
        fields = '__all__'

class EditProblemForm(ModelForm):
    class Meta:
	model = Problem
	fields = '__all___'
