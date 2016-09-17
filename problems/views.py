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

def SUGGESTED_PARADIGMS():
    return [str(tag.name) for tag in Category.objects.filter(type="paradigm")]

def add_paradigms(paradigms, problem):
    if problem.categories:
        remove_paradigms(problem)
    for p in paradigms.split(','):
        paradigm, c = Category.objects.get_or_create(name=p.strip().lower(), type="paradigm")
        problem.categories.add(paradigm)
        problem.save()

def remove_paradigms(problem):
    paradigms = problem.categories.all()
    for p in paradigms:
        problem.categories.remove(p)
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
    if solution.language:
        remove_languages(solution)
    for lang in langs.split(','):
        language, l = Category.objects.get_or_create(name=lang.strip().lower(), type="language")
        solution.language.add(language)
        solution.save()

def remove_languages(solution):
    languages = solution.language.all()
    for l in languages:
        solution.language.remove(l)
        solution.save()

def SUGGESTED_ALGORITHMS():
    return [str(alg.name) for alg in Category.objects.filter(type="algorithm")]

def add_algorithms(algorithms, solution):
    if solution.algorithms:
        remove_algorithms(solution)
    for a in algorithms.split(','):
        algorithm, a = Category.objects.get_or_create(name=a.strip().lower(), type="algorithm")
        solution.algorithms.add(algorithm)
        solution.save()

def remove_algorithms(solution):
    algorithms = solution.algorithms.all()
    for a in algorithms:
        solution.algorithms.remove(a)
        solution.save()

def SUGGESTED_DATA_STRUCTURES():
    return [str(ds.name) for ds in Category.objects.filter(type="data-structure")]

def add_ds(data_structures, solution):
    if solution.data_structures:
        remove_ds(solution)
    for ds in data_structures.split(','):
        data_structure, d = Category.objects.get_or_create(name=ds.strip().lower(), type="data-structure")
        solution.data_structures.add(data_structure)
        solution.save()

def remove_ds(solution):
    ds = solution.data_structures.all()
    for d in ds:
        solution.data_structures.remove(d)
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
        problems = Problem.objects.all()
        solutions = Solution.objects.all()

        #determine whether to return full index or a search results
        paradigms = request.GET.get('paradigms')
        languages = request.GET.get('languages')
        algorithms = request.GET.get('algorithms')
        complexity = request.GET.get('complexity')
        data_structures = request.GET.get('data_structures')
        difficulty = request.GET.get('difficulty')
        visibility = request.GET.get('visibility')

        #a normal index view should be the same as a search where all parameters are empty strings
        if request.user.is_authenticated():
            problems = self.auth_user_search(problems, solutions, paradigms, languages, complexity, algorithms, languages, difficulty, visibility)

            #only an authenticated user can edit and make challenges, so best have this here
            if challenge_id:
                challenge = get_object_or_404(Challenge, pk=challenge_id)
        else:
            problems = self.normal_search(problems, solutions, paradigms, languages, complexity, languages, difficulty, visibility)

        suggested_paradigms = SUGGESTED_PARADIGMS()
        suggested_data_structures = SUGGESTED_DATA_STRUCTURES()
        suggested_complexity = SUGGESTED_COMPLEXITY()
        suggested_algorithms = SUGGESTED_ALGORITHMS()
        suggested_languages = SUGGESTED_LANGUAGES()
        context = {
            'suggested_paradigms': suggested_paradigms,
            'suggested_data_structures': suggested_data_structures,
            'suggested_complexity': suggested_complexity,
            'suggested_algorithms': suggested_algorithms,
            'suggested_languages': suggested_languages,
            'problems': problems,
            'problem_sets': Challenge.objects.all(),
            'difficulties': zip(range(5),['Very Easy', 'Easy', 'Average', 'Difficult', 'Very Difficult']),
            'searched_paradigms': "" if paradigms==None else paradigms,
            'searched_algorithms': "" if algorithms==None else algorithms,
            'searched_complexity': "" if complexity==None else complexity,
            'searched_data_structures': "" if data_structures==None else data_structures,
            'searched_languages': "" if languages==None else languages,
            'searched_difficulty': "" if difficulty==None else difficulty,
            'searched_visibility': "" if visibility==None else visibility,
            'challenge': challenge,
        }
        return render(request, 'problems/index.html', context)

    def auth_user_search(self, problems, solutions, paradigms, data_structures, complexity, algorithms, languages, difficulty, visibility):
        #filter problem objects
        if paradigms:
            problems_by_cat = problems.filter(
                categories__name__in=[p.lower().strip() for p in paradigms.split(',')]
            ).distinct()
        else:
            problems_by_cat = problems
        if difficulty:
            problems_by_diff = problems.filter(difficulty=difficulty).distinct()
        else:
            problems_by_diff = problems
        filtered_problems = problems_by_cat|problems_by_diff
        if visibility == "private":
            problems_by_vis = problems.filter(problem_privacy=True)
            filtered_problems = filtered_problems|problems_by_vis
        elif visibility == "public":
            problems_by_vis = problems.filter(problem_privacy=False)
            filtered_problems = filtered_problems|problems_by_vis

        #filter solution objects
        if languages:
            solutions_by_lang = solutions.filter(
                language__name__in=[lang.lower().strip() for lang in languages.split(',')]
            ).distinct()
        else:
            solutions_by_lang = solutions
        if algorithms:
            solutions_by_alg = solutions.filter(
                algorithms__name__in=[alg.lower().strip() for alg in algorithms.split(',')]
            ).distinct()
        else:
            solutions_by_alg = solutions
        if complexity:
            solutions_by_c = solutions.filter(
                complexity__name__in=[c.lower().strip() for c in complexity.split(',')]
            ).distinct()
        else:
            solutions_by_c = solutions
        if data_structures:
            solutions_by_ds = solutions.filter(
                data_structures__name__in=[ds.lower().strip() for ds in data_structures.split(',')]
            ).distinct()
        else:
            solutions_by_ds  = solutions
        filtered_solutions = solutions_by_lang|solutions_by_alg|solutions_by_c|solutions_by_ds

        _problems = []

        for problem in filtered_problems.all():
            _problems.append(problem)
        for solution in filtered_solutions.all():
            if solution.problem not in _problems:
                _problems.append(solution.problem)
        return _problems

    def normal_search(self, problems, solutions, paradigms, data_structures, complexity, algorithms, languages, difficulty):
        #filter problem objects
        problems_by_cat = problems.filter(
            categories__name__in=[p.lower().strip() for p in paradigms.split(',')]
        ).distinct()
        problems_by_diff = problems.filter(difficulty=difficulty).distinct()
        problems_by_vis = problems.filter(problem_privacy=False).distinct()
        filtered_problems = problems_by_cat|problems_by_diff|problems_by_vis

        #filter solution objects
        solutions_by_lang = solutions.filter(
            language__name__in=[lang.lower().strip() for lang in languages.split(',')]
        ).distinct()
        solutions_by_alg = solutions.filter(
            algorithms__name__in=[alg.lower().strip() for alg in algorithms.split(',')]
        ).distinct()
        solutions_by_c = solutions.filter(
            complexity__name__in=[c.lower().strip() for c in complexity.split(',')]
        ).distinct()
        solutions_by_ds = solutions.filter(
            data_structures__name__in=[ds.lower().strip() for ds in data_structures.split(',')]
        ).distinct()
        filtered_solutions = solutions_by_lang|solutions_by_alg|solutions_by_c|solutions_by_ds

        _problems = []

        for problem in filtered_problems.all():
            _problems.append(problem)
        for solution in filtered_solutions.all():
            if solution.problem not in _problems and not solution.problem.problem_privacy:
                _problems.append(solution.problem)
        return _problems


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
        language_objects = solution.language.all()
        categories = []
        languages = []

        for category in category_objects:
            categories.append(category.name)

        for language in language_objects:
            languages.append(language.name)

        context = {
            'problem': problem,
            'content': content,
            'solution': solution,
            'challenge': challenge,
            'categories': categories,
            'languages': languages,
        }
        return render(request, 'problems/view_problem.html', context)


class Upload(View):

    method_decorator(login_required)
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
    method_decorator(login_required)
    def get(self, request):
        problem_form = ProblemForm()
        content_form = ContentForm()
        solution_form = SolutionForm()
        suggested_paradigms = SUGGESTED_PARADIGMS()
        suggested_algorithms = SUGGESTED_ALGORITHMS()
        suggested_data_structures = SUGGESTED_DATA_STRUCTURES()
        suggested_languages = SUGGESTED_LANGUAGES()
        suggested_complexity = SUGGESTED_COMPLEXITY()
        context = {
            'suggested_paradigms': suggested_paradigms,
            'suggested_algorithms': suggested_algorithms,
            'suggested_data_structures': suggested_data_structures,
            'suggested_languages': suggested_languages,
            'suggested_complexity': suggested_complexity,
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
        paradigms = request.POST.get('paradigms')
        algorithms = request.POST.get('algorithms')
        data_structures = request.POST.get('data_structures')

        if problem_form.is_valid() and content_form.is_valid() and solution_form.is_valid():
            problem = problem_form.save(commit=False)
            problem.created_by = request.user
            problem.save()
            if paradigms:
                add_paradigms(paradigms, problem)
            content = content_form.save(commit=False)
            content.problem = problem
            content.save()
            solution = solution_form.save(commit=False)
            solution.problem = problem
            if complexity:
                add_complexity(complexity, solution)
            if languages:
                add_language(languages, solution)
            if algorithms:
                add_algorithms(algorithms, solution)
            if data_structures:
                add_ds(data_structures, solution)
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
        paradigms = ",".join([p.name for p in problem.categories.all()])
        algorithms = ','.join([alg.name for alg in solution.algorithms.all()])
        data_structures = ','.join([ds.name for ds in solution.data_structures.all()])

        problem_form = ProblemForm(instance=problem)
        content_form = ContentForm(instance=content)
        solution_form = SolutionForm(instance=solution)

        suggested_paradigms = SUGGESTED_PARADIGMS()
        suggested_algorithms = SUGGESTED_ALGORITHMS()
        suggested_data_structures = SUGGESTED_DATA_STRUCTURES()
        suggested_languages = SUGGESTED_LANGUAGES()
        suggested_complexity = SUGGESTED_COMPLEXITY()
        context = {
            'suggested_paradigms': suggested_paradigms,
            'suggested_algorithms': suggested_algorithms,
            'suggested_data_structures': suggested_data_structures,
            'suggested_languages': suggested_languages,
            'suggested_complexity': suggested_complexity,
            'problem_form': problem_form,
            'content_form': content_form,
            'solution_form': solution_form,
            'complexity': complexity,
            'data_structures': data_structures,
            'paradigms': paradigms,
            'languages': languages,
            'algorithms': algorithms,
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
        paradigms = request.POST.get('paradigms')
        algorithms = request.POST.get('algorithms')
        data_structures = request.POST.get('data_structures')
        if problem_form.is_valid() and content_form.is_valid() and solution_form.is_valid():
            problem = problem_form.save()
            if paradigms:
                add_paradigms(paradigms, problem)
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
            if algorithms:
                add_algorithms(algorithms, solution)
            if data_structures:
                add_ds(data_structures, solution)
            solution.save()
            messages.success(request, 'Problem Edited')
        else:
            messages.error(request, 'Invalid Form')
        return redirect('index')


class ForkProblem(View):
    method_decorator(login_required)
    def get(self, request, problem_id):
        problem = Problem.objects.get(id=problem_id)
        content = Content.objects.get(problem=problem)
        solution = Solution.objects.get(problem=problem)
        complexity = solution.complexity
        languages = ','.join([lang.name for lang in solution.language.all()])
        data_structures = ','.join([ds.name for ds in solution.data_structures.all()])
        algorithms = ','.join([alg.name for alg in solution.algorithms.all()])
        paradigms = ",".join([p.name for p in problem.categories.all()])

        problem_form = ProblemForm(instance=problem)
        content_form = ContentForm(instance=content)
        solution_form = SolutionForm(instance=solution)

        suggested_paradigms = SUGGESTED_PARADIGMS()
        suggested_algorithms = SUGGESTED_ALGORITHMS()
        suggested_data_structures = SUGGESTED_DATA_STRUCTURES()
        suggested_languages = SUGGESTED_LANGUAGES()
        suggested_complexity = SUGGESTED_COMPLEXITY()
        context = {
            'suggested_paradigms': suggested_paradigms,
            'suggested_algorithms': suggested_algorithms,
            'suggested_data_structures': suggested_data_structures,
            'suggested_languages': suggested_languages,
            'suggested_complexity': suggested_complexity,
            'problem_form': problem_form,
            'content_form': content_form,
            'solution_form': solution_form,
            'complexity': complexity,
            'languages': languages,
            'paradigms': paradigms,
            'data_structures': data_structures,
            'algorithms': algorithms,
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
        paradigms = request.POST.get('paradigms')
        algorithms = request.POST.get('algorithms')
        data_structures = request.POST.get('data_structures')
        if problem_form.is_valid() and content_form.is_valid() and solution_form.is_valid():
            forked_problem = problem_form.save(commit=False)
            forked_problem.created_by = request.user
            forked_problem.pk = None
            forked_problem.forked_from = original_problem.title
            forked_problem.save()
            if paradigms:
                add_paradigms(paradigms, forked_problem)
            forked_content = content_form.save(commit=False)
            forked_content.pk = None
            forked_content.problem = forked_problem
            forked_content.save()
            forked_solution = solution_form.save(commit=False)
            forked_solution.pk = None
            forked_solution.problem = forked_problem
            forked_solution.save()
            if languages:
                add_language(languages, forked_solution)
            if complexity:
                add_complexity(complexity, forked_solution)
            if algorithms:
                add_algorithms(algorithms, forked_solution)
            if data_structures:
                add_ds(data_structures, forked_solution)
            messages.success(request, 'Problem Forked')
        else:
            messages.error(request, 'Invalid Form')
        return redirect('index')


class DeleteProblem(View):
    method_decorator(login_required)
    def post(self, request, problem_id):
        problem = Problem.objects.get(id=problem_id)
        Content.objects.get(problem=problem).delete()
        Solution.objects.get(problem=problem).delete()
        Problem.objects.get(id=problem_id).delete()
        return redirect('index')


class ChallengeIndex(View):
    method_decorator(login_required)
    def get(self, request):
        context = {
            'challenges': Challenge.objects.all(),
        }
        return render(request, 'problems/challenge_index.html', context)


class EditChallenge(View):
    method_decorator(login_required)
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
    method_decorator(login_required)
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
    method_decorator(login_required)
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
    method_decorator(login_required)
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
