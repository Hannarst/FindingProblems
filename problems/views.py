from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.views.generic import View, UpdateView
from models import *
from forms import *
from django.contrib import messages

def AddCategory(categories, problem):
    for cat in categories.split(','):
        category, c = Category.objects.get_or_create(name=cat.strip().lower())
        problem.categories.add(category)
        problem.save()

class Index(View):
     def get(self, request):
        problems = Problem.objects
        categories = request.GET.get('categories')
        difficulty = request.GET.get('difficulty')
        privacy = request.GET.get('privacy')
        if categories:
            problems = problems.filter(
                categories__name__in=[x.lower().strip() for x in categories.split(',')]).distinct()
        else:
            categories = ""
        if difficulty:
            difficulty = int(difficulty)
            problems = problems.filter(difficulty=difficulty)
        if privacy == "private":
            problems = problems.filter(private=true)
        elif privacy == "public":
            problems = problems.filter(private=false)
        context = {
            'problems': problems.all(),
            'difficulties': Problem.DIFFICULTIES,
            'searched_categories': categories,
            'searched_difficulty': difficulty,
            'searched_privacy': privacy,
        }
        return render(request, 'problems/index.html', context)

class AddProblem(View):
    def get(self, request):
        problem_form = ProblemForm()
        categories_form = CategoriesForm()
        context = {
            'problem_form': problem_form,
            'categories_form': categories_form,
        }
        return render(request, 'problems/add_problem.html', context)

    def post(self, request):
        problem_form = ProblemForm(request.POST)
        categories_form = CategoriesForm(request.POST)
        if problem_form.is_valid() and categories_form.is_valid():
            problem = problem_form.save()
            AddCategory(request.POST.get('categories'), problem)
            messages.success(request, 'Problem Added')
        else:
            messages.error(request, 'Invalid Form')
        return redirect('index')

class EditProblem(UpdateView):
    form_class = ProblemForm
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
	form = ProblemForm(instance=problem)
	context = {
	    'form': form,
	}
	return render(request, 'problems/edit_problem.html', context)

    def post(self, request, problem_id):
	form = ProblemForm(request.POST)
	if form.is_valid():
	    forked_problem = form.save(commit=False)
	    forked_problem.pk = None
	    forked_problem.save()
	    messages.success(request, 'Problem Forked')
	else:
	    messages.error(request, 'Invalid Form')
	return redirect('index')
