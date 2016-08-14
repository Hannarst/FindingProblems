from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.views.generic import View, UpdateView
from models import *
from forms import *
from django.contrib import messages

def add_category(categories, problem):
    for cat in categories.split(','):
        category, c = Category.objects.get_or_create(name=cat.strip().lower())
        problem.categories.add(category)
        problem.save()

class Index(View):
     def get(self, request):
        challenge_id = request.session.get('challenge_id', "")
        challenge = ""
        problems = Problem.objects
        categories = request.GET.get('categories')
        difficulty = request.GET.get('difficulty')
        privacy = request.GET.get('privacy')
        if challenge_id:
            challenge = get_object_or_404(
                Challenge, pk=challenge_id)
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
            'challenge': challenge,
        }
        return render(request, 'problems/index.html', context)

class ViewProblem(View):
    def get(self, request, problem_id):
        challenge_id = request.session.get('challenge_id', "")
        challenge = ""
        if challenge_id:
            challenge = get_object_or_404(Challenge, pk=challenge_id)
        context = {
            'problem': Problem.objects.get(pk=problem_id),
            'challenge': challenge,
        }
        return render(request, 'problems/view_problem.html', context)

class AddProblem(View):
    def get(self, request):
        problem_form = ProblemForm()
        categories_form = CategoriesForm()
        context = {
            'form': problem_form,
        }
        return render(request, 'problems/add_problem.html', context)

    def post(self, request):
        problem_form = ProblemForm(request.POST)
        categories = request.POST.get('categories')
        if problem_form.is_valid() and categories:
            problem = problem_form.save()
            add_category(categories, problem)
            messages.success(request, 'Problem Added')
        else:
            messages.error(request, 'Invalid Form')
        return redirect('index')

class EditProblem(View):
    def get(self, request, problem_id):
    	problem = Problem.objects.get(id=problem_id)
        categories = ",".join([cat.name for cat in problem.categories.all()])
    	form = ProblemForm(instance=problem)
    	context = {
    	    'form': form,
            'categories': categories,
    	}
    	return render(request, 'problems/edit_problem.html', context)

    def post(self, request, problem_id):
        problem = Problem.objects.get(id=problem_id)
    	form = ProblemForm(request.POST, instance=problem)
        categories = request.POST.get('categories')
    	if form.is_valid() and categories:
    	    problem = form.save(commit=False)
    	    problem.save()
            add_category(categories, problem)
    	    messages.success(request, 'Problem Edited')
    	else:
    	    messages.error(request, 'Invalid Form')
    	return redirect('index')


class ForkProblem(View):
    def get(self, request, problem_id):
    	problem = Problem.objects.get(id=problem_id)
        categories = ",".join([cat.name for cat in problem.categories.all()])
    	form = ProblemForm(instance=problem)
    	context = {
    	    'form': form,
            'categories': categories,
    	}
	return render(request, 'problems/edit_problem.html', context)

    def post(self, request, problem_id):
    	form = ProblemForm(request.POST)
        categories = request.POST.get('categories')
    	if form.is_valid() and categories:
    	    forked_problem = form.save(commit=False)
            forked_problem.pk = None
    	    forked_problem.save()
            add_category(categories, forked_problem)
    	    messages.success(request, 'Problem Forked')
    	else:
    	    messages.error(request, 'Invalid Form')
    	return redirect('index')

class ChallengeIndex(View):
     def get(self, request):
        context = {
            'challenges': Challenge.objects.all(),
        }
        return render(request, 'problems/challenge_index.html', context)


class EditChallenge(View):
    def get(self, request, challenge_id):
    	challenge = Challenge.objects.get(id=challenge_id)
        form = ChallengeForm(instance=challenge)
    	context = {
    	    'form': form,
    	}
    	return render(request, 'problems/edit_challenge.html', context)

    def post(self, request, challenge_id):
        challenge = Challenge.objects.get(id=challenge_id)
    	form = ChallengeForm(request.POST, instance=challenge)
        if form.is_valid():
    	    challenge = form.save()
            messages.success(request, 'Challenge Edited')
    	else:
    	    messages.error(request, 'Invalid Form')
    	return redirect('challenge_index')


class ViewChallenge(View):
    def get(self, request, challenge_id):
        context = {
            'challenge': Challenge.objects.get(pk=challenge_id),
        }
        return render(request, 'problems/view_challenge.html', context)

    def post(self, request, challenge_id):
        # remove problems
        pass

class AddChallenge(View):
    def get(self, request):
        form = ChallengeForm()
        context = {
            'form': form,
        }
        return render(request, 'problems/add_challenge.html', context)

    def post(self, request):
        form = ChallengeForm(request.POST)
        if form.is_valid():
            problem = form.save()
            request.session['challenge_id'] = problem.id
            messages.success(request, 'Challenge Created')
        else:
            messages.error(request, 'Invalid Form')
        return redirect('index')
