import os
from hashlib import md5

from io import StringIO, BytesIO

import collections
from itertools import islice

from PyPDF2 import PdfFileReader
import random
import datetime
import reportlab
from django.contrib.auth.models import User
from django.core.files.storage import FileSystemStorage
from django.core.mail import send_mail
from django.core.management import call_command
from django.forms import formset_factory
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.shortcuts import render, redirect, get_object_or_404
from django.template import Context
from django.template.loader import get_template
from django.utils.datastructures import MultiValueDictKeyError
from django.views.generic import View
from django.contrib import messages
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required, user_passes_test

from FindingProblems import settings
from .models import *
from .forms import *

def is_activated(user):
    """
    A method decorator test. Determines whether or not a user has activated their account.
    :param user: User object
    :return: True if the Account has been activated, otherwise False
    """
    acc = Account.objects.get(user=user)
    return acc.activated


class HelperView(View):
    """
    A class to containing some functionality common to a number of views.
    """
    def SUGGESTED_PARADIGMS(self):
        """
        Suggested paradigms for auto-completion
        :return: A list of the names of Category objects of type paradigm already in the system
        """
        return [str(tag.name) for tag in Category.objects.filter(type="paradigm")]

    def SUGGESTED_COMPLEXITY(self):
        """
        Suggested complexities for auto-completion
        :return: A list of the names of Category objects of type complexity already in the system
        """
        return [str(tag.name) for tag in Category.objects.filter(type="complexity")]

    def SUGGESTED_LANGUAGES(self):
        """
        Suggested languages for auto-completion
        :return: A list of the names of Category objects of type language already in the system
        """
        return [str(lang.name) for lang in Category.objects.filter(type="language")]

    def SUGGESTED_ALGORITHMS(self):
        """
        Suggested algorithms for auto-completion
        :return: A list of the names of Category objects of type algorithm already in the system
        """
        return [str(alg.name) for alg in Category.objects.filter(type="algorithm")]

    def SUGGESTED_DATA_STRUCTURES(self):
        """
        Suggested data_structures for auto-completion
        :return: A list of the names of Category objects of type data-structure already in the system
        """
        return [str(ds.name) for ds in Category.objects.filter(type="data-structure")]


class Home(View):
    """
    A view for managing requests made to the Home page
    """
    def get(self, request):
        """
        A method for handling HTTP GET requests made to the Home page
        :param request: A dictionary object representing the HTTP GET request
        :return: Returns an HTTP response object which renders the Home page
        """
        return render(request, 'problems/home.html')


class Guide(View):
    """
    A view for managing requests made to the Guide page
    """
    def get(self, request):
        """
        A method for handling HTTP GET requests made to the Guide page
        :param request: A dictionary object representing the HTTP GET request
        :return: Returns an HTTP response object which renders the Guide page
        """
        return render(request, 'problems/guide.html')


class ActivateAccount(View):
    """
    A class for managing requests to the Activate Account page
    """
    @method_decorator(login_required)
    def get(self, request):
        """
        A method for handling HTTP GET requests made to the Activate Account page
        :param request: A dictionary object representing the HTTP GET request
        :return: Returns an HTTP response object which renders the Activate Account page
        """
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
        """
        A method for handling HTTP POST requests made to the Home page
        :param request: A dictionary object representing the HTTP POST request
        :return: Returns an HTTP response object which renders the Problem Catalogue page. If an error occurs a response
        object representing the Activate Account page is returned instead.
        """
        user = request.user
        activation_code = request.POST['activation_code']
        account = get_object_or_404(Account, user=user)
        today = datetime.date.today()
        context = {
            'deadline_valid': False,
            'code_valid': False,
            'form': ActivateAccountForm(),
        }

        # check that the account can still be activated using this code
        if today <= account.activation_deadline:
            context['deadline_valid'] = True
            if activation_code == account.activation_code:
                account.activated = True
                account.save()
                return redirect('/problems/')
            else:
                return render(request, 'problems/activate_account.html', context)
        # else, reset the activation code and don't allow
        else:
            account.reset_activation_code()
            return render(request, 'problems/activate_account.html', context)


class CreateAccount(View):
    """
    A class for managing requests made to the Create Account page
    """
    def get(self, request):
        """
        A method for handling HTTP GET requests made to the Create Account page
        :param request: A dictionary object representing the HTTP GET request
        :return: Returns an HTTP response object which renders the Create Account page
        """
        account_form = CreateAccountForm()
        context = {
            'form': account_form
        }

        return render(request, 'problems/create_account.html', context)

    def post(self, request):
        """
        A method for handling HTTP POST requests made to the Create Account page
        :param request: A dictionary object representing the HTTP POST request
        :return: Returns an HTTP response object which renders the New Account page. If an error occurs, the Create
        Account page is rendered instead.
        """
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
        """
        Creates a date for activation date deadline
        :return: A datetime.date object representing the new deadline
        """
        today = datetime.date.today()
        deadline = today + datetime.timedelta(days=7)
        return deadline

    def create_activation_code(self):
        """
        Creates an activation code for a user
        :return: An alpha-numeric String made up of 20 characters
        """
        random_string = str(random.random()).encode('utf-8')
        _hash = md5(random_string).hexdigest()
        activation_code = _hash[:20]
        return activation_code

    def create_user(self, post_info):
        """
        Creates a new User object for an Account
        :param post_info: A dictionary representing the HTTP POST request sent to the class
        :return: A new instance of the User model
        """
        username = post_info['email']
        pwd = post_info['password_one']
        user = User()
        user.username = username
        user.email = username
        user.set_password(pwd)
        user.save()
        return user

    def create_account(self, post_info):
        """
        Creates a new instance of the Account model
        :param post_info: A dictionary representing the HTTP POST request sent to the class
        :return: Sends an email to the user.
        """
        # setup user stuff
        user = self.create_user(post_info)
        # setup activation stuff
        activation_code = self.create_activation_code()
        activation_deadline = self.create_date()
        # create account
        account = Account()
        account.user = user
        account.activation_code = activation_code
        account.activation_deadline = activation_deadline
        account.save()
        send_mail(
            'Activation code for FindingProblems.com',
            'Please use the following code to activate your account when you first log into the website: ' + str(
                account.activation_code),
            'findingproblemstest@gmail.com',
            [account.user.username],
            fail_silently=False,
        )


class Index(HelperView):
    """
    A class for managing requests made to the Problem Catalogue page
    """
    def get(self, request):
        """
        A method for handling HTTP GET requests made to the Problem Catalogue page
        :param request: A dictionary object representing the HTTP GET request
        :return: Returns an HTTP response object which renders the Problem Catalogue page
        """
        challenge_id = request.session.get('challenge_id', "")
        problems = Problem.objects.all()
        solutions = Solution.objects.all()
        challenge = ""
        # determine whether to return full index or a search results
        paradigms = request.GET.get('paradigms', '')
        languages = request.GET.get('languages', '')
        algorithms = request.GET.get('algorithms', '')
        complexity = request.GET.get('complexity', '')
        data_structures = request.GET.get('data_structures', '')
        difficulty = request.GET.get('difficulty', '')
        visibility = request.GET.get('visibility', '')

        #filter the problems by the terms in the search query
        if paradigms:
            problems = problems.filter(categories__name__in=[x.lower().strip() for x in paradigms.split(',')])
        if languages:
            problems = problems.filter(solution__language__name__in=[x.lower().strip() for x in languages.split(',')])
        if algorithms:
            problems = problems.filter(solution__algorithms__name__in=[x.lower().strip() for x in algorithms.split(',')])
        if complexity:
            problems = problems.filter(solution__complexity__name__in=[x.lower().strip() for x in complexity.split(',')])
        if data_structures:
            problems = problems.filter(solution__data_structures__name__in=[x.lower().strip() for x in data_structures.split(',')])
        if difficulty:
            problems = problems.filter(difficulty=difficulty)

        if request.user.is_authenticated() and is_activated(request.user):
            if visibility:
                problems = problems.filter(problem_privacy=(visibility=="private"))
            if challenge_id:
                challenge = Challenge.objects.get(pk=challenge_id)
        else:
            problems = problems.exclude(problem_privacy=True)

        problems_tuples = self.get_problem_data(problems)
        context = {
            'suggested_paradigms': self.SUGGESTED_PARADIGMS(),
            'suggested_data_structures': self.SUGGESTED_DATA_STRUCTURES(),
            'suggested_complexity': self.SUGGESTED_COMPLEXITY(),
            'suggested_algorithms': self.SUGGESTED_ALGORITHMS(),
            'suggested_languages': self.SUGGESTED_LANGUAGES(),
            'problems': problems.distinct(),
            'problem_info': problems_tuples,
            'problem_sets': Challenge.objects.all(),
            'difficulties': zip(range(5), ['Very Easy', 'Easy', 'Average', 'Difficult', 'Very Difficult']),
            'searched_paradigms': paradigms,
            'searched_algorithms': algorithms,
            'searched_complexity': complexity,
            'searched_data_structures': data_structures,
            'searched_languages': languages,
            'searched_difficulty': difficulty,
            'searched_visibility': visibility,
            'challenge': challenge,
        }
        return render(request, 'problems/index.html', context)

    def get_solution_availability(self, solution):
        """
        A helper method for determining the state of the solution availability for a particular problem
        :param solution: the solution whose state of availability needs to be determined
        :return: the state of availability of a solution. Either 'No solution provided', True (publicaly viewable), or
        False (privately viewable)
        """
        if solution.all_defaults():
            return 'No solution provided.'
        else:
            return solution.solution_privacy

    def get_problem_data(self, problems):
        """
        A helper method for rendering information on the Problem Catalogue page.
        :param problems: The set of problems for which data needs to be obtained.
        :return: A tuple representing the state of the following pieces of information (problem id, solution availability, categories for the problem)
        """
        p_list = []
        for problem in problems:
            solution = Solution.objects.get(problem=problem)
            solution_availability = self.get_solution_availability(solution)
            categories = solution.get_all_categories()
            temp = (problem.id, solution_availability, categories)
            p_list.append(temp)
        return p_list


class ViewProblem(View):
    def get(self, request, problem_id):
        challenge_id = request.session.get('challenge_id', "")
        challenge = ""
        if challenge_id:
            challenge = get_object_or_404(Challenge, pk=challenge_id)

        problem = Problem.objects.get(pk=problem_id)
        content = Content.objects.get(problem=problem)
        solution = Solution.objects.get(problem=problem)
        complexity = [c.name for c in solution.complexity.all()]
        languages = [lang.name for lang in solution.language.all()]
        paradigms = [p.name for p in problem.categories.all()]
        algorithms = [alg.name for alg in solution.algorithms.all()]
        data_structures = [ds.name for ds in solution.data_structures.all()]

        context = {
            'problem': problem,
            'content': content,
            'solution': solution,
            'challenge': challenge,
            'complexity': complexity,
            'data_structures': data_structures,
            'paradigms': paradigms,
            'languages': languages,
            'algorithms': algorithms,
        }
        return render(request, 'problems/view_problem.html', context)


class AddProblemFromPDF(HelperView):
    """
    A class for managing requests made to the Upload Problem via PDF page
    """
    @method_decorator(login_required)
    @method_decorator(user_passes_test(is_activated, login_url="/problems/accounts/activate/"))
    def get(self, request):
        """
        A method for handling HTTP GET requests made to the Upload Problem via PDF page
        :param request: A dictionary object representing the HTTP GET request
        :return: Returns an HTTP response object which renders the Upload Problem via PDF page
        """
        pdf_form = PDFForm()
        context = {
            'pdf_form': pdf_form,
        }
        return render(request, 'problems/upload.html', context)

    def post(self, request):
        """
        A method for handling HTTP POST requests made to the Upload Problem via PDF page
        :param request: A dictionary object representing the HTTP POST request
        :return: Returns an HTTP response object which renders the Add Problem form with the information from the uploaded
        PDF. If an error occurs, it renders the Problem Catalogue page with an error message displayed.
        """
        pdf_form = PDFForm(request.POST, request.FILES)
        if pdf_form.is_valid():
            if request.FILES:
                #process the problem PDF, if it exists
                try:
                    if request.FILES['problem']:
                        problem_file = request.FILES['problem']
                        fs = FileSystemStorage()
                        f_name = fs.save(problem_file.name, problem_file)
                        f_name = f_name.replace('%20', ' ')
                        #upload the file
                        upload_file_url = settings.MEDIA_ROOT+'\\'+f_name
                        #parse the file
                        parsed_problem_pdf = self.parse_problem_pdf(upload_file_url)
                        problem_form = parsed_problem_pdf[0]
                        paradigms = parsed_problem_pdf[1]
                        content_form = parsed_problem_pdf[2]
                        os.remove(upload_file_url)

                #set up default problem and content form
                except MultiValueDictKeyError:
                    p_form_data = {
                        'title': '',
                    }
                    problem_form = ProblemForm(initial=p_form_data)
                    paradigms = ''
                    c_form_data = {
                        'problem_description': '',
                        'example_input': 'No example input provided.',
                        'example_output': 'No example output provided.',
                    }
                    content_form = ContentForm(initial=c_form_data)

                #process the solution PDF, if it exists
                try:
                    if request.FILES['solution']:
                        solution_file = request.FILES['solution']
                        fs = FileSystemStorage()
                        f_name = fs.save(solution_file.name, solution_file)
                        f_name = f_name.replace('%20', ' ')
                        #upload the file
                        upload_file_url = settings.MEDIA_ROOT+'\\'+f_name
                        #parse the file
                        parsed_solution_pdf = self.parse_solution_pdf(upload_file_url)
                        solution_form = parsed_solution_pdf[0]
                        languages = parsed_solution_pdf[1]
                        algorithms = parsed_solution_pdf[2]
                        data_structures = parsed_solution_pdf[3]
                        complexity = parsed_solution_pdf[4]
                        os.remove(upload_file_url)

                #set up default solution form
                except MultiValueDictKeyError:
                    s_form_data = {
                        'solution_description': 'No solution description has been provided.',
                        'links': 'No links.',
                        'example_code': 'No example solution code.',
                        'time_limit': 0,
                        'complexity': None,
                    }
                    solution_form = SolutionForm(s_form_data)
                    languages = ''
                    algorithms = ''
                    data_structures = ''
                    complexity = ''
            #if neither file submitted, setup default problem, content and solution forms
            else:
                p_form_data = {
                    'title': '',
                }
                problem_form = ProblemForm(initial=p_form_data)
                c_form_data = {
                    'problem_description': '',
                    'example_input': 'No example input provided.',
                    'example_output': 'No example output provided.',
                }
                content_form = ContentForm(initial=c_form_data)
                s_form_data = {
                    'solution_description': '',
                    'links': 'No links.',
                    'example_code': 'No example solution code.',
                    'time_limit': 0,
                    'complexity': None,
                }
                solution_form = SolutionForm(s_form_data)
                paradigms = ''
                languages = ''
                algorithms = ''
                data_structures = ''
                complexity = ''

            context = {
                'problem_form': problem_form,
                'content_form': content_form,
                'solution_form': solution_form,
                'paradigms': paradigms,
                'languages': languages,
                'algorithms': algorithms,
                'data_structures': data_structures,
                'complexity': complexity,
                'suggested_paradigms': self.SUGGESTED_PARADIGMS,
                'suggested_algorithms': self.SUGGESTED_ALGORITHMS,
                'suggested_data_structures': self.SUGGESTED_DATA_STRUCTURES,
                'suggested_languages': self.SUGGESTED_LANGUAGES,
                'suggested_complexity': self.SUGGESTED_COMPLEXITY,
            }
            messages.info(request, "File has been uploaded. Please check to make sure that all the fields are correct.")
            return render(request, 'problems/add_problem_from_pdf.html', context)
        else:
            messages.info(request, "Error when uploading file. Please try again.")
            return redirect('index')

    def parse_solution_pdf(self, file_name):
        """
        A helper method for parsing a PDF containing the solution to a problem
        :param file_name: The name of the file to be parsed.
        :return: A list, containing the following [populated solution form, string representing the languages by which the
        solution has been categorised, a string representing the algorithms by which the solution has been categorised,
        a string representing the data structures by which the solution has been categorised, a string representing the
        complexities by which the solution has been categorised]
        """
        HEADINGS = ['complexity', 'links', 'time limit', 'example code', 'languages', 'algorithms', 'data structures']
        solution_pdf_content = self.getPDFContent(file_name)
        #parse the solution description
        solution_description = ""
        start_next_section = 0
        if solution_pdf_content[start_next_section] not in HEADINGS:
            for line in range(0, len(solution_pdf_content)):
                if solution_pdf_content[line].lower() in HEADINGS:
                    start_next_section = line
                    break
                else:
                    solution_description += solution_pdf_content[line] + '\n'
        complexity = ""
        links = ""
        example_code = ""
        language = ""
        data_structures = ""
        algorithms = ""
        time_limit = ""

        max_index = len(solution_pdf_content) - 1
        not_end_of_file = True
        #parse the subsections of the file based on expected HEADINGS
        while not_end_of_file:
            if solution_pdf_content[start_next_section].lower() == 'complexity':
                start = start_next_section + 1
                for line in range(start, len(solution_pdf_content)):
                    if solution_pdf_content[line].lower() in HEADINGS:
                        break
                    else:
                        complexity += solution_pdf_content[line] + '\n'
                        start_next_section += 1
            elif solution_pdf_content[start_next_section].lower() == 'links':
                start = start_next_section + 1
                for line in range(start, len(solution_pdf_content)):
                    if solution_pdf_content[line].lower() in HEADINGS:
                        break
                    else:
                        links += solution_pdf_content[line] + '\n'
                        start_next_section += 1
            elif solution_pdf_content[start_next_section].lower() == 'example code':
                start = start_next_section + 1
                for line in range(start, len(solution_pdf_content)):
                    if solution_pdf_content[line].lower() in HEADINGS:
                        break
                    else:
                        example_code += solution_pdf_content[line] + '\n'
                        start_next_section += 1
            elif solution_pdf_content[start_next_section].lower() == 'languages':
                start = start_next_section + 1
                for line in range(start, len(solution_pdf_content)):
                    if solution_pdf_content[line].lower() in HEADINGS:
                        break
                    else:
                        language += solution_pdf_content[line] + ','
                        start_next_section += 1
            elif solution_pdf_content[start_next_section].lower() == 'data structures':
                start = start_next_section + 1
                for line in range(start, len(solution_pdf_content)):
                    if solution_pdf_content[line].lower() in HEADINGS:
                        break
                    else:
                        data_structures += solution_pdf_content[line] + ','
                        start_next_section += 1
            elif solution_pdf_content[start_next_section].lower() == 'algorithms':
                start = start_next_section + 1
                for line in range(start, len(solution_pdf_content)):
                    if solution_pdf_content[line].lower() in HEADINGS:
                        break
                    else:
                        algorithms += solution_pdf_content[line] + ','
                        start_next_section += 1
            elif solution_pdf_content[start_next_section].lower() == 'time limit':
                start = start_next_section + 1
                for line in range(start, len(solution_pdf_content)):
                    if solution_pdf_content[line].lower() in HEADINGS:
                        break
                    else:
                        time_limit += solution_pdf_content[line] + ','
                        start_next_section += 1
            start_next_section += 1
            if start_next_section >= max_index:
                not_end_of_file = False

        reject_char = [' ', '', '\n']
        # clean up languages
        temp_language = ""
        for l in language.split(','):
            if l in reject_char:
                pass
            else:
                temp_language += l + ','
        language = temp_language[:-1]
        # clean up complexity
        temp_complexity = ""
        for c in complexity.split(','):
            if c in reject_char:
                pass
            else:
                temp_complexity += c + ','
        complexity = temp_complexity[:-1]
        # clean up datastructures input
        temp_ds = ""
        for ds in data_structures.split(','):
            if ds in reject_char:
                pass
            else:
                temp_ds += ds + ','
        data_structures = temp_ds[:-1]
        # clean up time limit input
        for char in time_limit:
            try:
                int(char)
            except ValueError:
                if char == '.':
                    pass
                else:
                    time_limit = time_limit.replace(char, '')
        if time_limit == '.':
            time_limit = float(0)

        #populate the solution form
        s_form_data = {
            'solution_description': solution_description if solution_description != "" else "No solution description has been provided.",
            'links': links.strip() if links != "" else "No links.",
            'example_code': example_code if example_code != "" else "No example solution code.",
            'time_limit': time_limit if time_limit != "" else 0,
        }
        solution_form = SolutionForm(initial=s_form_data)
        return [solution_form, language.strip(), algorithms.strip(), data_structures.strip(), complexity.strip()]

    def parse_problem_pdf(self, file_name):
        """
        A helper method for parsing a PDF of a problem
        :param file_name: The name of the file containing the problem
        :return: A list containing the following values: [populated problem form, paradigms by which the problem should
        be categorised, populated content form]
        """
        HEADINGS = ['sample input', 'problem description', 'sample output', 'paradigms']
        problem_pdf_content = self.getPDFContent(file_name)
        title = problem_pdf_content[0]
        #parse the problem description
        problem_description = ""
        start_next_section = 1
        sample_input = ""
        sample_output = ""
        paradigms = ""
        max_index = len(problem_pdf_content) - 1
        not_end_of_file = True
        #parse the rest of the file based on expected HEADINGS
        while not_end_of_file:
            if problem_pdf_content[start_next_section].lower() == 'sample input':
                start = start_next_section + 1
                for line in range(start, len(problem_pdf_content)):
                    if problem_pdf_content[line].lower() in HEADINGS:
                        break
                    else:
                        sample_input += problem_pdf_content[line] + '\n'
                        start_next_section += 1
            elif problem_pdf_content[start_next_section].lower() == 'problem description':
                start = start_next_section + 1
                for line in range(start, len(problem_pdf_content)):
                    if problem_pdf_content[line].lower() in HEADINGS:
                        break
                    else:
                        problem_description += problem_pdf_content[line] + '\n'
                        start_next_section += 1
            elif problem_pdf_content[start_next_section].lower() == 'sample output':
                start = start_next_section + 1
                for line in range(start, len(problem_pdf_content)):
                    if problem_pdf_content[line].lower() in HEADINGS:
                        break
                    else:
                        sample_output += problem_pdf_content[line] + '\n'
                        start_next_section += 1
            elif problem_pdf_content[start_next_section].lower() == 'paradigms':
                start = start_next_section + 1
                for line in range(start, len(problem_pdf_content)):
                    if problem_pdf_content[line].lower() in HEADINGS:
                        break
                    else:
                        paradigms += problem_pdf_content[line] + '\n'
                        start_next_section += 1
            start_next_section += 1
            if start_next_section >= max_index:
                not_end_of_file = False

        #populate the problem form
        p_form_data = {
            'title': title,
        }
        problem_form = ProblemForm(initial=p_form_data)
        #populate the content form
        c_form_data = {
            'problem_description': problem_description,
            'example_input': sample_input if sample_input != "" else "No sample input provided.",
            'example_output': sample_output if sample_output != "" else "No sample output provided.",
        }
        content_form = ContentForm(initial=c_form_data)

        return [problem_form, paradigms, content_form]

    def consume(self, iterator, num):
        """
        A helper method to increment the current iteration of a loop
        :param iterator: An Iterator for a loop
        :param num: The number of iterations the Iterator needs to be moved through
        :return: The incremented iterator
        """
        if num is None:
            collections.deque(iterator, maxlen=0)
        else:
            next(islice(iterator, num, num), None)

    def getPDFContent(self, file_name):
        """
        A helper method for reading and saving information from the PDF
        :param file_name: The name of the file to be read in
        :return: A list containing the contents of the PDF on a line- by-line basis
        """
        pdf_file = open(file_name, 'rb')
        reader = PdfFileReader(pdf_file)
        actual_lines = []
        pages = reader.getNumPages()
        for page in range(pages):
            current_page = reader.getPage(page).extractText()
            list_of_lines = current_page.split('\n')
            out_of_range = len(list_of_lines)
            max_index = out_of_range - 1
            lines_on_page = iter(range(out_of_range))
            for line in lines_on_page:
                section = list_of_lines[line]
                # end of file, just append the line
                if line == max_index:
                    actual_lines.append(section)
                # otherwise
                else:
                    next_section = list_of_lines[line + 1]
                    # if the next line is just a blank line, append both and continue from the line after the blank one
                    if list_of_lines[line + 1] == ' ':
                        actual_lines.append(section)
                        actual_lines.append(next_section)
                        self.consume(lines_on_page, 1)
                    else:
                        temp_line = line
                        paragraph = ""
                        while section != ' ':
                            paragraph += section
                            temp_line += 1
                            if temp_line <= max_index:
                                section = list_of_lines[temp_line]
                            else:
                                break
                        actual_lines.append(paragraph)
                        self.consume(lines_on_page, temp_line - line)

        pdf_file.close()
        return actual_lines


class AddProblem(HelperView):
    """
    A class for managing requests made to the Add Problem page
    """
    @method_decorator(login_required)
    @method_decorator(user_passes_test(is_activated, login_url="/problems/accounts/activate/"))
    def get(self, request):
        """
        A method for managing HTTP GET requests made to the Add Problem page
        :param request: A dictionary representing the HTTP GET request
        :return: An HTTP response object rendering the Add Problem page
        """
        problem_form = ProblemForm()
        content_form = ContentForm()
        solution_form = SolutionForm()
        suggested_paradigms = self.SUGGESTED_PARADIGMS()
        suggested_algorithms = self.SUGGESTED_ALGORITHMS()
        suggested_data_structures = self.SUGGESTED_DATA_STRUCTURES()
        suggested_languages = self.SUGGESTED_LANGUAGES()
        suggested_complexity = self.SUGGESTED_COMPLEXITY()
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
        """
        A method for managing HTTP POST requests made to the Add Problem page
        :param request: A dictionary representing the HTTP POST request
        :return: An HTTP response object rendering the Problem Catalogue page. If an error occurs, an error message is
        displayed
        """
        #get the relevant data
        problem_form = ProblemForm(request.POST)
        content_form = ContentForm(request.POST)
        solution_form = SolutionForm(request.POST)
        time_limit = request.POST.get('time_limit')
        complexity = request.POST.get('complexity')
        languages = request.POST.get('languages')
        paradigms = request.POST.get('paradigms')
        algorithms = request.POST.get('algorithms')
        data_structures = request.POST.get('data_structures')

        #validate the data
        if problem_form.is_valid() and content_form.is_valid() and solution_form.is_valid():
            #use the data to create new instances of the models
            problem = problem_form.save(commit=False)
            problem.created_by = request.user
            problem.save()
            if paradigms:
                problem.add_paradigms(paradigms)
            content = content_form.save(commit=False)
            content.problem = problem
            content.save()
            solution = solution_form.save(commit=False)
            solution.time_limit = time_limit if time_limit else 0
            solution.problem = problem
            solution.save()
            if complexity:
                solution.add_complexity(complexity)
            if languages:
                solution.add_language(languages)
            if algorithms:
                solution.add_algorithms(algorithms)
            if data_structures:
                solution.add_ds(data_structures)
            messages.success(request, 'Problem Added')
        else:
            messages.error(request, 'Invalid Form')
        return redirect('index')


class EditProblem(HelperView):
    """
    A class for managing the requests made to the Edit Problem page
    """
    @method_decorator(login_required)
    @method_decorator(user_passes_test(is_activated, login_url="/problems/accounts/activate/"))
    def get(self, request, problem_id):
        """
        A method for handling HTTP GET requests to the Edit Problem page
        :param request: A dictionary respresenting the HTTP GET request
        :param problem_id: The unique identifier for the problem to be edited
        :return: An HTTP response object to render to the Edit Problem page
        """
        #retrive the relevant data to render the page
        problem = Problem.objects.get(id=problem_id)
        content = Content.objects.get(problem=problem)
        solution = Solution.objects.get(problem=problem)
        complexity = ','.join([c.name for c in solution.complexity.all()])
        languages = ','.join([lang.name for lang in solution.language.all()])
        paradigms = ",".join([p.name for p in problem.categories.all()])
        algorithms = ','.join([alg.name for alg in solution.algorithms.all()])
        data_structures = ','.join([ds.name for ds in solution.data_structures.all()])

        problem_form = ProblemForm(instance=problem)
        content_form = ContentForm(instance=content)
        solution_form = SolutionForm(instance=solution)

        suggested_paradigms = self.SUGGESTED_PARADIGMS()
        suggested_algorithms = self.SUGGESTED_ALGORITHMS()
        suggested_data_structures = self.SUGGESTED_DATA_STRUCTURES()
        suggested_languages = self.SUGGESTED_LANGUAGES()
        suggested_complexity = self.SUGGESTED_COMPLEXITY()
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
        """
        A method for handling HTTP POST requests
        :param request: A dictionary representing the HTTP POST request
        :param problem_id: The unique identifier for the problem to be edited
        :return: An HTTP response object which renders the Problem Catelogue page. If an error occurs, an error
        message is displayed.
        """
        #retrieve the edited information
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
        #ensure the data is valid
        if problem_form.is_valid() and content_form.is_valid() and solution_form.is_valid():
            #update the relevant objects
            edited_problem = problem_form.save()
            prev_par = ','.join([p.name for p in problem.categories.all()])
            if paradigms!=prev_par:
                edited_problem.add_paradigms(paradigms)
            content = content_form.save(commit=False)
            content.problem = edited_problem
            content.save()
            edited_solution = solution_form.save(commit=False)
            edited_solution.problem = edited_problem
            prev_complexity = ','.join([c.name for c in solution.complexity.all()])
            if complexity!=prev_complexity:
                edited_solution.add_complexity(complexity)
            prev_lang = ','.join([l.name for l in solution.language.all()])
            if languages!=prev_lang:
                edited_solution.add_language(languages)
            prev_alg = ','.join([a.name for a in solution.algorithms.all()])
            if algorithms!=prev_alg:
                edited_solution.add_algorithms(algorithms)
            prev_ds = ','.join([ds.name for ds in solution.data_structures.all()])
            if data_structures!=prev_ds:
                edited_solution.add_ds(data_structures)
            edited_solution.save()
            messages.success(request, 'Problem Edited')
        else:
            messages.error(request, 'Invalid Form')
        return redirect('index')


class ForkProblem(HelperView):
    """
    A class for managing requests made to the Fork Problem page
    """
    @method_decorator(login_required)
    @method_decorator(user_passes_test(is_activated, login_url="/problems/accounts/activate/"))
    def get(self, request, problem_id):
        problem = Problem.objects.get(id=problem_id)
        content = Content.objects.get(problem=problem)
        solution = Solution.objects.get(problem=problem)
        complexity = ','.join([c.name for c in solution.complexity.all()])
        languages = ','.join([lang.name for lang in solution.language.all()])
        data_structures = ','.join([ds.name for ds in solution.data_structures.all()])
        algorithms = ','.join([alg.name for alg in solution.algorithms.all()])
        paradigms = ",".join([p.name for p in problem.categories.all()])

        problem_form = ProblemForm(instance=problem)
        content_form = ContentForm(instance=content)
        solution_form = SolutionForm(instance=solution)

        suggested_paradigms = self.SUGGESTED_PARADIGMS()
        suggested_algorithms = self.SUGGESTED_ALGORITHMS()
        suggested_data_structures = self.SUGGESTED_DATA_STRUCTURES()
        suggested_languages = self.SUGGESTED_LANGUAGES()
        suggested_complexity = self.SUGGESTED_COMPLEXITY()
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
                forked_problem.add_paradigms(paradigms)
            forked_content = content_form.save(commit=False)
            forked_content.pk = None
            forked_content.problem = forked_problem
            forked_content.save()
            forked_solution = solution_form.save(commit=False)
            forked_solution.pk = None
            forked_solution.problem = forked_problem
            forked_solution.save()
            if languages:
                forked_solution.add_language(languages)
            if complexity:
                forked_solution.add_complexity(complexity)
            if algorithms:
                forked_solution.add_algorithms(algorithms)
            if data_structures:
                forked_solution.add_ds(data_structures)
            messages.success(request, 'Problem Forked')
        else:
            messages.error(request, 'Invalid Form')
        return redirect('index')


class DeleteProblem(View):
    """
    A class for managing requests made to the Delete Problem page
    """
    @method_decorator(login_required)
    @method_decorator(user_passes_test(is_activated, login_url="/problems/accounts/activate/"))
    def post(self, request, problem_id):
        """
        A method for handling HTTP POST requests made to the Delete Problem page
        :param request: A dictionary representing the HTTP POST request
        :param problem_id: The unique identifier for the problem which is to be deleted
        :return: An HTTP object representing the Problem Catalogue page. If an error occurs, the view of the problem is
        rendered
        """
        problem = Problem.objects.get(id=problem_id)
        if request.user == problem.created_by:
            Content.objects.get(problem=problem).delete()
            Solution.objects.get(problem=problem).delete()
            Problem.objects.get(id=problem_id).delete()
            return redirect('index')
        else:
            content = Content.objects.get(problem=problem)
            solution = Solution.object.get(problem=problem)
            challenge_id = request.session.get('challenge_id', "")
            challenge = ""
            if challenge_id:
                challenge = get_object_or_404(Challenge, pk=challenge_id)
            complexity = [c.name for c in solution.complexity.all()]
            languages = [lang.name for lang in solution.language.all()]
            paradigms = [p.name for p in problem.categories.all()]
            algorithms = [alg.name for alg in solution.algorithms.all()]
            data_structures = [ds.name for ds in solution.data_structures.all()]
            context = {
                'problem': problem,
                'content': content,
                'solution': solution,
                'challenge': challenge,
                'complexity': complexity,
                'data_structures': data_structures,
                'paradigms': paradigms,
                'languages': languages,
                'algorithms': algorithms,
            }
            messages.error(request, 'You are not allowed to delete this problem.')
            return render(request, 'problems/view_problem.html', context)


class ChallengeIndex(View):
    """
    A class for handling requests made to the Challenge Catalogue page
    """
    @method_decorator(login_required)
    @method_decorator(user_passes_test(is_activated, login_url="/problems/accounts/activate/"))
    def get(self, request):
        """
        A method for handling HTTP GET requests made to the Challenge Catalogue page
        :param request: A dictionary represnting the HTTP GET requst
        :return: An HTTP response object which renders the Challenge Catalogue page
        """
        context = {
            'challenges': Challenge.objects.all(),
        }
        return render(request, 'problems/challenge_index.html', context)


class EditChallenge(View):
    """
    A class for handling requests made to the Edit Challenge page
    """
    @method_decorator(login_required)
    @method_decorator(user_passes_test(is_activated, login_url="/problems/accounts/activate/"))
    def get(self, request, challenge_id):
        """
        A method for handling HTTP GET requests made to the Edit Challenge page
        :param request: A dictionary representing the HTTP GET request
        :param challenge_id: The unique identifier for the challenge from which a problem is to be edited
        :return: An HTTP response object which renders the Challenge Catalogue page
        """
        challenge = Challenge.objects.get(id=challenge_id)
        form = ChallengeForm(instance=challenge)
        context = {
            'form': form,
        }
        return render(request, 'problems/view_challenge.html', context)

    def post(self, request, challenge_id):
        """
        A method for handling HTTP POST requests made to the Edit Challenge page
        :param request: A dictionary representing the HTTP POST request
        :param challenge_id: The unique identifier for the challenge from which a problem is to be edited
        :return: An HTTP response object which renders the Challenge Catalogue page. If an error occurs the system
        displays an error message.
        """
        challenge = Challenge.objects.get(id=challenge_id)
        form = ChallengeForm(request.POST, instance=challenge)
        if form.is_valid():
            challenge = form.save()
            messages.success(request, 'Challenge Edited')
        else:
            messages.error(request, 'Invalid Form')
        return redirect('challenge_index')


class ViewChallenge(View):
    """
    A class for handling requests made to the View Challenge page
    """
    @method_decorator(login_required)
    @method_decorator(user_passes_test(is_activated, login_url="/problems/accounts/activate/"))
    def get(self, request, challenge_id):
        """
        A method for handling HTTP GET requests made to the View Challenge page
        :param request: A dictionary represnting the HTTP GET request
        :param challenge_id: The unique identifier for the challenge which is to be viewed
        :return: An HTTP response object which renders the View Challenge page
        """
        request.session['challenge_id'] = challenge_id
        context = {
            'challenge2': Challenge.objects.get(pk=challenge_id),
        }
        return render(request, 'problems/view_challenge.html', context)


class QuitEditingChallenge(View):
    """
    A class for handling requests made to the Quit Editing Challenge page
    """
    @method_decorator(login_required)
    @method_decorator(user_passes_test(is_activated, login_url="/problems/accounts/activate/"))
    def get(self, request):
        """
        A method for handling HTTP GET requests made to the Remove from Challenge page
        :param request: A dictionary represnting the HTTP GET request
        :return: An HTTP response object which renders the previous page
        """
        request.session['challenge_id'] = None
        return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))

    def post(self, request):
        """
        A method for handling HTTP POST requests made to the Remove from Challenge page
        :param request: A dictionary represnting the HTTP POST request
        :return: An HTTP response object which renders the previous page
        """
        request.session['challenge_id'] = None
        return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))


class AddChallenge(View):
    """
    A class for handling requests made to the Add Challenge page
    """
    @method_decorator(login_required)
    @method_decorator(user_passes_test(is_activated, login_url="/problems/accounts/activate/"))
    def get(self, request):
        """
        A method for handling HTTP GET requests made to the Add Challenge page
        :param request: A dictionary representing the HTTP GET request
        :return: An HTTP response object which renders the Add Challenge page.
        """
        form = ChallengeForm()
        context = {
            'form': form,
        }
        return render(request, 'problems/add_challenge.html', context)

    def post(self, request):
        """
        A method for handling HTTP POST requests made to the Add Challenge page
        :param request: A dictionary representing the HTTP POST request
        :return: An HTTP response object which renders the Problem Catalogue page. If an error occurs and the Challenge
        is not added an error message is displayed.
        """
        form = ChallengeForm(request.POST)
        if form.is_valid():
            challenge = form.save()
            request.session['challenge_id'] = challenge.id
            messages.success(request, 'Challenge Created')
        else:
            messages.error(request, 'Invalid Form')
        return redirect('index')


class AddToChallenge(View):
    """
    A class for handling requests made to the Add To Challenge page
    """
    @method_decorator(login_required)
    @method_decorator(user_passes_test(is_activated, login_url="/problems/accounts/activate/"))
    def post(self, request, challenge_id, problem_id):
        """
        A method for handling HTTP POST requests made to the Add To hallenge page
        :param request: A dictionary representing the HTTP POST request
        :param challenge_id: The unique identifier for the challenge to which a problem is to be added
        :param problem_id: The unique identifier for the problem which is to be added to the challenge
        :return: An HTTP response object which renders the Problem Catalogue page
        """
        challenge = Challenge.objects.get(pk=challenge_id)
        challenge.problems.add(Problem.objects.get(pk=problem_id))
        challenge.save()
        return redirect('index')


class RemoveFromChallenge(View):
    """
    A class for handling requests made to the Remove From Challenge page
    """
    @method_decorator(login_required)
    @method_decorator(user_passes_test(is_activated, login_url="/problems/accounts/activate/"))
    def post(self, request, challenge_id, problem_id):
        """
        A method for handling HTTP POST requests made to the Remove from Challenge page
        :param request: A dictionary representing the HTTP POST request
        :param challenge_id: The unique identifier for the challenge from which a problem is to be removed
        :param problem_id: The unique identifier for the problem which is to be removed from the challenge
        :return: An HTTP response object which renders the Problem Catalogue page
        """
        challenge = Challenge.objects.get(pk=challenge_id)
        challenge.problems.remove(Problem.objects.get(pk=problem_id))
        challenge.save()
        return redirect('index')
