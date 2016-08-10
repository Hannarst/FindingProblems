from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.views.generic import View, UpdateView
from models import *
from forms import *
from django.contrib import messages

class Index(View):
     def get(self, request):
        problems = Problem.objects.all()
        context = {
            'problems': problems,
        }
        return render(request, 'problems/index.html', context)

class AddProblem(View):
    def get(self, request):
        form = ProblemForm()
        context = {
            'form': form,
        }
        return render(request, 'problems/add_problem.html', context)

    def post(self, request):
        form = ProblemForm(request.POST)
        if form.is_valid():
            post = form.save()
            messages.success(request, 'Problem Added')
        else:
            messages.error(request, 'Invalid Form')
        return redirect('index')

class EditProblem(UpdateView):
    form_class = EditProblemForm
    model = Problem
    fields = '__all__'
    template_name = 'problems/edit_form.html'

    def get(self, request, **kwargs):
	self.object = Problem.objects.get(id=self.kwargs['id'])
	form_class = self.get_form_class()
	form = self.get_form(form_class)
	context = self.get_context_data(object=self.object, form=form)
	return self.render_to_response(context)

    def get_object(self, queryset=None):
	obj = Problem.objects.get(id=self.kwargs['id'])
	return obj

class ForkProblem(View):
    def get(self, request, problem_id):
	problem = Problem.objects.get(id=problem_id)
	form = EditProblemForm(instance=problem)
	context = {
	    'form': form,
	}
	return render(request, 'problems/edit_problem.html', context)

    def post(self, request, problem_id):
	form = EditProblemForm(request.POST)
	if form.is_valid():
	    forked_problem = form.save(commit=False)
	    forked_problem.pk = None
	    forked_problem.save()
	    messages.success(request, 'Problem Forked')
	else:
	    messages.error(request, 'Invalid Form')
	return redirect('index')
