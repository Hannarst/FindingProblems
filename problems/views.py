from hashlib import md5
import random
import datetime
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.http import HttpResponseRedirect
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import View
from models import *
from forms import *
from django.contrib import messages

def add_category(categories, problem):
    for cat in categories.split(','):
        category, c = Category.objects.get_or_create(name=cat.strip().lower())
        problem.categories.add(category)
        problem.save()

class ActivateAccount(View):
    def get(self, request):
        activate_account_form = ActivateAccountForm()
        context = {
            'form': activate_account_form
        }
        return render(request, 'problems/activate_account.html', context)

    def post(self, request):
        user = request.user
        activation_code = request.POST['activation_code']
        account = get_object_or_404(Account, user=user)
        today = datetime.date.today()
        context = {
            'deadline_valid': False,
            'code_valid': False
        }

        #check that the account can still be activated using this code
        if today <= account.activation_deadline:
           context['deadline_valid'] = True
           if activation_code == account.activation_code:
               account.user.is_active = True
               account.user.save()
               account.save()
               return HttpResponseRedirect('problems/')
           else:
               return render(request, 'problems/activate_account.html', context)
        #else, reset the activation code and don't allow
        else:
            account.reset_activation_code()
            return render(request, 'problems/activate_account.html', context)


class CreateAccount(View):
    def get(self, request):
        account_form = CreateAccountForm()
        context = {
            'form': account_form
        }

        return render(request, 'problems/create_account.html', context)

    def post(self, request):
        account_form = CreateAccountForm(request.POST or None)
        context = {
            'email': request.POST['email'],
            'created': False,
            'form': account_form
        }
        if account_form.is_valid():
            self.create_account(request.POST)
            context['created'] = True
            return render(request, 'problems/new_account.html', context)
        messages.error(request, 'Account not created.')
        return render(request, 'problems/create_account.html', context)

    def create_date(self):
        today = datetime.date.today()
        deadline = today + datetime.timedelta(days=7)
        return deadline

    def create_activation_code(self):
        random_float = random.random()
        _hash = md5(str(random_float)).hexdigest()
        activation_code = _hash[:20]
        return activation_code

    def create_user(self, post_info):
        username = post_info['email']
        pwd = post_info['password_one']
        user = User()
        user.username = username
        user.set_password(pwd)
        user.is_active = False
        user.save()
        return user

    def create_account(self, post_info):
        #setup user stuff
        user = self.create_user(post_info)
        #setup activation stuff
        activation_code = self.create_activation_code()
        activation_deadline = self.create_date()
        #create account
        account = Account()
        account.user = user
        account.activation_code = activation_code
        account.activation_deadline = activation_deadline
        account.save()
        send_mail(
            'Activation code for FindingProblems.com',
            'Please use the following code to activate your account when you first log into the website: '+str(account.activation_code),
            'findingproblemstest@gmail.com',
            [account.user.username],
            fail_silently=False,
            )


class Index(View):
     def get(self, request):
        challenge_id = request.session.get('challenge_id', "")
        challenge = ""
        problems = Problem.objects
        categories = request.GET.get('categories')
        difficulty = request.GET.get('difficulty')
        privacy = request.GET.get('privacy')
        if challenge_id:
            challenge = get_object_or_404(Challenge, pk=challenge_id)
        if categories:
            problems = problems.filter(
                categories__name__in=[x.lower().strip() for x in categories.split(',')]).distinct()
        else:
            categories = ""
        if difficulty:
            difficulty = int(difficulty)
            problems = problems.filter(difficulty=difficulty)
        if privacy == "private":
            problems = problems.filter(private=True)
        elif privacy == "public":
            problems = problems.filter(private=False)
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
        original_problem = Problem.objects.get(id=problem_id)
        categories = request.POST.get('categories')
    	if form.is_valid() and categories:
    	    forked_problem = form.save(commit=False)
            forked_problem.pk = None
            forked_problem.forked_from = original_problem.title
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
    	return render(request, 'problems/view_challenge.html', context)

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
        request.session['challenge_id'] = challenge_id
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
            challenge = form.save()
            request.session['challenge_id'] = challenge.id
            messages.success(request, 'Challenge Created')
        else:
            messages.error(request, 'Invalid Form')
        return redirect('index')


class AddToChallenge(View):
    def post(self, request, challenge_id, problem_id):
        challenge = Challenge.objects.get(pk=challenge_id)
        challenge.problems.add(Problem.objects.get(pk=problem_id))
        challenge.save()
        return redirect('index')


class RemoveFromChallenge(View):
    def post(self, request, challenge_id, problem_id):
        challenge = Challenge.objects.get(pk=challenge_id)
        challenge.problems.remove(Problem.objects.get(pk=problem_id))
        challenge.save()
        return redirect('index')
