from hashlib import md5

from io import StringIO

import collections
from itertools import islice

from PyPDF2 import PdfFileReader
import random
import datetime
import reportlab
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.forms import formset_factory
from django.http import HttpResponseRedirect
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import View
from .models import *
from .forms import *
from django.contrib import messages
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required


def SUGGESTED_TAGS():
    return [str(tag.name) for tag in Category.objects.filter(type="tag")]

def add_category(categories, problem):
    for cat in categories.split(','):
        category, c = Category.objects.get_or_create(name=cat.strip().lower())
        problem.categories.add(category)
        problem.save()

def SUGGESTED_COMPLEXITY():
    return [str(tag.name) for tag in Category.objects.filter(type="complexity")]

def add_complexity(complexity, solution):
    complex, c = Category.objects.get_or_create(name=complexity.strip().lower(), type="complexity")
    solution.complexity = complex
    solution.save()

def SUGGESTED_LANGUAGES():
    return [str(lang.name) for lang in Category.objects.filter(type="language")]

def add_language(langs, solution):
    for lang in langs.split(','):
        language, l = Category.objects.get_or_create(name=lang.strip().lower())
        solution.language.add(language)
        solution.save()

def remove_languages(solution):
    languages = solution.language.all()
    for l in languages:
        solution.language.remove(l)
        solution.save()

class Home(View):
    def get(self, request):
        return render(request, 'problems/home.html')


class Guide(View):
    def get (self, request):
        return render(request, 'problems/guide.html')


class ActivateAccount(View):
    def get(self, request):
        account = get_object_or_404(Account, user=request.user)
        if account.activated:
            return redirect('/problems/')
        else:
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
                account.activated = True
                account.save()
                return redirect('/problems/')
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
        random_string = str(random.random()).encode('utf-8')
        _hash = md5(random_string).hexdigest()
        activation_code = _hash[:20]
        return activation_code

    def create_user(self, post_info):
        username = post_info['email']
        pwd = post_info['password_one']
        user = User()
        user.username = username
        user.email = username
        user.set_password(pwd)
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
            solutions_complexity = Solution.objects.filter(
                complexity__name__in=[x.lower().strip() for x in categories.split(',')],
            ).distinct()
            solutions_language = Solution.objects.filter(
                language__name__in=[x.lower().strip() for x in categories.split(',')],
            ).distinct()
            solutions = solutions_complexity|solutions_language
            problems = problems.filter(
                categories__name__in=[x.lower().strip() for x in categories.split(',')],
            ).distinct()
        else:
            categories = ""
        if difficulty:
            difficulty = int(difficulty)
            problems = problems.filter(difficulty=difficulty)
        if privacy == "private":
            problems = problems.filter(private=True)
        elif privacy == "public":
            problems = problems.filter(private=False)

        if request.user.is_authenticated():
            temp_problems = problems.all()
            problems = []
            for problem in temp_problems:
                problems.append(problem)
            if categories:
                solutions = solutions.all()
                for solution in solutions:
                    problems.append(Problem.objects.get(pk=solution.problem.pk))
        else:
            temp_problems = problems.exclude(private=True)
            problems = []
            for problem in temp_problems:
                problems.append(problem)
            if categories:
                solutions = solutions.all()
                for solution in solutions:
                    p = Problem.objects.get(pk=solution.problem.pk)
                    if p.private:
                        pass
                    else:
                        problems.append(p)
        suggested_tags = SUGGESTED_TAGS()+SUGGESTED_COMPLEXITY()+SUGGESTED_LANGUAGES()
        context = {
            'suggested_tags': suggested_tags,
            'problems': problems,
            'difficulties': zip(range(5),['Very Easy', 'Easy', 'Average', 'Difficult', 'Very Difficult']),
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

        problem = Problem.objects.get(pk=problem_id)
        content = Content.objects.get(problem=problem)
        solution = Solution.objects.get(problem=problem)
        category_objects = problem.categories.all()
        categories = []

        for category in category_objects:
            categories.append(category.name)

        context = {
            'problem': problem,
            'content': content,
            'solution': solution,
            'challenge': challenge,
            'categories': categories,
        }
        return render(request, 'problems/view_problem.html', context)


class Upload(View):
    def get(self, request):
        pdf_form = PDFForm()
        context = {
            'pdf_form': pdf_form,
        }
        return render(request, 'problems/upload.html', context)

    def post(self, request):
        pdf_form = PDFForm(request.POST, request.FILES)
        if pdf_form.is_valid():
            if request.FILES['problem']:
                parsed_problem_pdf = self.parse_problem_pdf(pdf_form)
                problem = parsed_problem_pdf[0]
                problem_form = parsed_problem_pdf[1]
                content_form = parsed_problem_pdf[2]

            if request.FILES['solution']:
                parsed_solution_pdf = self.parse_solution_pdf(pdf_form, problem)
                solution_form = parsed_solution_pdf[0]

            context = {
                'problem': problem,
                'problem_form': problem_form,
                'content_form': content_form,
                'solution_form': solution_form,
                'categories': ",".join([cat.name for cat in problem.categories.all()]),
            }
            messages.info(request, "File has been uploaded. Please check to make sure that all the fields are correct.")
            return render(request, 'problems/add_problem_from_pdf.html', context)
        else:
            messages.info(request, "Error when uploading file. Please try again.")
            return redirect('index')

    def parse_solution_pdf(self, pdf_form, problem):
        HEADINGS = ['complexity', 'links', 'example code', 'language']
        file_name = self.get_file_name(str(pdf_form.cleaned_data['solution']))[0]
        solution_pdf_content = self.getPDFContent(file_name)
        solution_description = ""
        start_next_section = 1
        if solution_pdf_content[start_next_section] not in HEADINGS:
            for line in range(1, len(solution_pdf_content)):
                if solution_pdf_content[line].lower() in HEADINGS:
                    start_next_section = line
                    break
                else:
                    solution_description += solution_pdf_content[line]+'\n'
        complexity = ""
        links = ""
        example_code = ""
        language = ""

        max_index = len(solution_pdf_content)-1
        not_end_of_file = True
        while not_end_of_file:
            if solution_pdf_content[start_next_section].lower() == 'complexity':
                start = start_next_section+1
                for line in range(start, len(solution_pdf_content)):
                    if solution_pdf_content[line].lower() in HEADINGS:
                        break
                    else:
                        complexity += solution_pdf_content[line]+'\n'
                        start_next_section += 1
            elif solution_pdf_content[start_next_section].lower() == 'links':
                start = start_next_section+1
                for line in range(start, len(solution_pdf_content)):
                    if solution_pdf_content[line].lower() in HEADINGS:
                        break
                    else:
                        links += solution_pdf_content[line]+'\n'
                        start_next_section += 1
            elif solution_pdf_content[start_next_section].lower() == 'example code':
                start = start_next_section+1
                for line in range(start, len(solution_pdf_content)):
                    if solution_pdf_content[line].lower() in HEADINGS:
                        break
                    else:
                        example_code += solution_pdf_content[line]+'\n'
                        start_next_section += 1
            elif solution_pdf_content[start_next_section].lower() == 'language':
                start = start_next_section+1
                for line in range(start, len(solution_pdf_content)):
                    if solution_pdf_content[line].lower() in HEADINGS:
                        break
                    else:
                        language += solution_pdf_content[line]+'\n'
                        start_next_section += 1
            start_next_section += 1
            if start_next_section >= max_index:
                not_end_of_file = False

        solution = Solution()
        solution.problem = problem
        if solution_description != "":
            solution.solution_description = solution_description
        if complexity != "":
            add_complexity(complexity, solution)
        if links != "":
            solution.links = links
        if example_code != "":
            solution.example_code = example_code
        if language != "":
            solution.language = language
        solution.save()
        solution_form = SolutionForm(instance=solution)

        return [solution_form]

    def parse_problem_pdf(self, pdf_form):
        HEADINGS = ['sample input', 'sample output', 'categories']
        file_name = self.get_file_name(str(pdf_form.cleaned_data['problem']))[0]
        problem_pdf_content = self.getPDFContent(file_name)
        title = problem_pdf_content[0]
        problem_description = ""
        start_next_section = 1
        if problem_pdf_content[start_next_section] not in HEADINGS:
            for line in range(1, len(problem_pdf_content)):
                if problem_pdf_content[line].lower() in HEADINGS:
                    start_next_section = line
                    break
                else:
                    problem_description += problem_pdf_content[line]+'\n'
        sample_input = ""
        sample_output = ""
        categories = ""
        max_index = len(problem_pdf_content)-1
        not_end_of_file = True
        while not_end_of_file:
            if problem_pdf_content[start_next_section].lower() == 'sample input':
                start = start_next_section+1
                for line in range(start, len(problem_pdf_content)):
                    if problem_pdf_content[line].lower() in HEADINGS:
                        break
                    else:
                        sample_input += problem_pdf_content[line]+'\n'
                        start_next_section += 1
            elif problem_pdf_content[start_next_section].lower() == 'sample output':
                start = start_next_section+1
                for line in range(start, len(problem_pdf_content)):
                    if problem_pdf_content[line].lower() in HEADINGS:
                        break
                    else:
                        sample_output += problem_pdf_content[line]+'\n'
                        start_next_section += 1
            elif problem_pdf_content[start_next_section].lower() == 'categories':
                start = start_next_section+1
                for line in range(start, len(problem_pdf_content)):
                    if problem_pdf_content[line].lower() in HEADINGS:
                        break
                    else:
                        categories += problem_pdf_content[line]+'\n'
                        start_next_section += 1
            start_next_section += 1
            if start_next_section >= max_index:
                not_end_of_file = False

        problem = Problem()
        problem.title = title +" unique mothafucka. I said unique!"
        problem.save()
        if categories != "":
            add_category(categories, problem)
        problem_form = ProblemForm(instance=problem)
        content = Content()
        content.problem_description = problem_description
        content.problem = problem
        if sample_input != "":
            content.example_input = sample_input
        if sample_output != "":
            content.example_output = sample_output
        content.save()
        content_form = ContentForm(instance=content)

        return [problem, problem_form, content_form]

    def get_file_name(self, file):
        return file.split('<In MemoryUploadedFile: ')

    def consume(self, iterator, num):
        if num is None:
            collections.deque(iterator, maxlen=0)
        else:
            next(islice(iterator, num, num), None)

    def getPDFContent(self, file_name):
        pdf_file = open(file_name, 'rb')
        reader = PdfFileReader(pdf_file)
        actual_lines = []
        pages = reader.getNumPages()
        for page in range(pages):
            current_page = reader.getPage(page).extractText()
            list_of_lines = current_page.split('\n')
            out_of_range = len(list_of_lines)
            max_index = out_of_range-1
            lines_on_page = iter(range(out_of_range))
            for line in lines_on_page:
                section = list_of_lines[line]
                #end of file, just append the line
                if line == max_index:
                    actual_lines.append(section)
                #otherwise
                else:
                    next_section = list_of_lines[line+1]
                    #if the next line is just a blank line, append both and continue from the line after the blank one
                    if list_of_lines[line+1] == ' ':
                        actual_lines.append(section)
                        actual_lines.append(next_section)
                        self.consume(lines_on_page, 1)
                    else:
                        temp_line = line
                        paragraph = ""
                        while section != ' ':
                            paragraph+=section
                            temp_line += 1
                            section = list_of_lines[temp_line]
                        actual_lines.append(paragraph)
                        self.consume(lines_on_page, temp_line-line)

        pdf_file.close()
        return actual_lines


class AddProblem(View):
    @method_decorator(login_required)
    def get(self, request):
        problem_form = ProblemForm()
        content_form = ContentForm()
        solution_form = SolutionForm()
        suggested_tags = SUGGESTED_COMPLEXITY()+SUGGESTED_TAGS()+SUGGESTED_LANGUAGES()
        context = {
            'suggested_tags': suggested_tags,
            'problem_form': problem_form,
            'content_form': content_form,
            'solution_form': solution_form
        }
        return render(request, 'problems/add_problem.html', context)

    def post(self, request):
        problem_form = ProblemForm(request.POST)
        content_form = ContentForm(request.POST)
        solution_form = SolutionForm(request.POST)
        complexity = request.POST.get('complexity')
        languages = request.POST.get('languages')
        categories = request.POST.get('categories')

        if problem_form.is_valid() and content_form.is_valid() and solution_form.is_valid() and categories:
            problem = problem_form.save()
            add_category(categories, problem)
            content = content_form.save(commit=False)
            content.problem = problem
            content.save()
            solution = solution_form.save(commit=False)
            solution.problem = problem
            if complexity:
                add_complexity(complexity, solution)
            if languages:
                add_language(languages, solution)
            solution.save()
            messages.success(request, 'Problem Added')
        else:
            messages.error(request, 'Invalid Form')
        return redirect('index')


class EditProblem(View):
    @method_decorator(login_required)
    def get(self, request, problem_id):
        problem = Problem.objects.get(id=problem_id)
        content = Content.objects.get(problem=problem)
        solution = Solution.objects.get(problem=problem)
        complexity = solution.complexity
        languages = ','.join([lang.name for lang in solution.language.all()])
        categories = ",".join([cat.name for cat in problem.categories.all()])

        problem_form = ProblemForm(instance=problem)
        content_form = ContentForm(instance=content)
        solution_form = SolutionForm(instance=solution)

        suggested_tags = SUGGESTED_COMPLEXITY()+SUGGESTED_TAGS()+SUGGESTED_LANGUAGES()
        context = {
            'suggested_tags': suggested_tags,
            'suggested_complexity': SUGGESTED_COMPLEXITY,
            'problem_form': problem_form,
            'content_form': content_form,
            'solution_form': solution_form,
            'complexity': complexity.name,
            'languages': languages,
            'categories': categories,
        }
        return render(request, 'problems/edit_problem.html', context)

    def post(self, request, problem_id):
        problem = Problem.objects.get(id=problem_id)
        content = Content.objects.get(problem=problem)
        solution = Solution.objects.get(problem=problem)
        problem_form = ProblemForm(request.POST, instance=problem)
        content_form = ContentForm(request.POST, instance=content)
        solution_form = SolutionForm(request.POST, instance=solution)
        complexity = request.POST.get('complexity')
        languages = request.POST.get('languages')
        print(languages)
        categories = request.POST.get('categories')
        if problem_form.is_valid() and content_form.is_valid() and solution_form.is_valid() and categories:
            problem = problem_form.save()
            add_category(categories, problem)
            content = content_form.save(commit=False)
            content.problem = problem
            content.save()
            solution = solution_form.save(commit=False)
            solution.problem = problem
            if complexity:
                add_complexity(complexity, solution)
            if languages:
                remove_languages(solution)
                add_language(languages, solution)
            solution.save()
            messages.success(request, 'Problem Edited')
        else:
            messages.error(request, 'Invalid Form')
        return redirect('index')


class ForkProblem(View):
    @method_decorator(login_required)
    def get(self, request, problem_id):
        problem = Problem.objects.get(id=problem_id)
        content = Content.objects.get(problem=problem)
        solution = Solution.objects.get(problem=problem)
        complexity = solution.complexity
        languages = ','.join([lang.name for lang in solution.language.all()])
        categories = ",".join([cat.name for cat in problem.categories.all()])

        problem_form = ProblemForm(instance=problem)
        content_form = ContentForm(instance=content)
        solution_form = SolutionForm(instance=solution)

        suggested_tags = SUGGESTED_COMPLEXITY()+SUGGESTED_TAGS()+SUGGESTED_LANGUAGES()
        context = {
            'suggested_tags': suggested_tags,
            'problem_form': problem_form,
            'content_form': content_form,
            'solution_form': solution_form,
            'complexity': complexity.name,
            'languages': languages,
            'categories': categories,
            'fork': True,
        }
        return render(request, 'problems/edit_problem.html', context)

    def post(self, request, problem_id):
        original_problem = Problem.objects.get(id=problem_id)
        problem_form = ProblemForm(request.POST)
        content_form = ContentForm(request.POST)
        solution_form = SolutionForm(request.POST)
        complexity = request.POST.get('complexity')
        languages = request.POST.get('languages')
        categories = request.POST.get('categories')
        if problem_form.is_valid() and content_form.is_valid() and solution_form.is_valid() and categories:
            forked_problem = problem_form.save(commit=False)
            forked_problem.pk = None
            forked_problem.forked_from = original_problem.title
            forked_problem.save()
            add_category(categories, forked_problem)
            forked_content = content_form.save(commit=False)
            forked_content.pk = None
            forked_content.problem = forked_problem
            forked_content.save()
            forked_solution = solution_form.save(commit=False)
            forked_solution.pk = None
            forked_solution.problem = forked_problem
            if languages:
                add_complexity(complexity, forked_solution)
                add_language(languages, forked_solution)
            else:
                add_complexity(complexity, forked_solution)
            forked_solution.save()
            messages.success(request, 'Problem Forked')
        else:
            messages.error(request, 'Invalid Form')
        return redirect('index')


class ChallengeIndex(View):
    @method_decorator(login_required)
    def get(self, request):
        context = {
            'challenges': Challenge.objects.all(),
        }
        return render(request, 'problems/challenge_index.html', context)


class EditChallenge(View):
    @method_decorator(login_required)
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
    @method_decorator(login_required)
    def get(self, request, challenge_id):
        request.session['challenge_id'] = challenge_id
        context = {
            'challenge2': Challenge.objects.get(pk=challenge_id),
        }
        return render(request, 'problems/view_challenge.html', context)

    def post(self, request, challenge_id):
        # remove problems
        pass


class QuitEditingChallenge(View):
    def get(self, request):
        request.session['challenge_id'] = None
        return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))

    def post(self, request):
        request.session['challenge_id'] = None
        return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))


class AddChallenge(View):
    @method_decorator(login_required)
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
    @method_decorator(login_required)
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
