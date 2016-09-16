from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.db import models
from .models import *

class LoginForm(AuthenticationForm):
    username = forms.CharField(label="Username", max_length=30,
                               widget=forms.TextInput(attrs={'class': 'form-control',
                                                             'name': 'username'}))
    password = forms.CharField(label="Password", max_length=30,
                               widget=forms.PasswordInput())


class ActivateAccountForm(forms.Form):
    activation_code = forms.CharField(label="Activation Code:", max_length=20)


class CreateAccountForm(forms.Form):
    email = forms.EmailField(label="UCT Computer Science Department staff email address:", max_length=300,
                              widget=forms.EmailInput())
    password_one = forms.CharField(label="Password:", max_length=30,
                               widget=forms.PasswordInput())
    password_two = forms.CharField(label="Re-enter password:", max_length=30,
                                   widget=forms.PasswordInput())

    def clean(self):
        form_data = self.cleaned_data
        #passwords must match
        if form_data['password_one'] != form_data['password_two']:
            self._errors["password_one"] = ["Passwords do not match"] # Will raise a error message
            self._errors["password_two"] = ["Passwords do not match"]
            del form_data['password_one']
            del form_data['password_two']
        #email must be that of a uct cs department member
        if form_data['email'].split('@')[1]!="gmail.com":
            self._errors["email"] = ["Email is not a valid UCT Computer Science department staff email address."]
            del form_data["email"]
        return form_data


class SolutionForm(forms.ModelForm):
    class Meta:
        model = Solution
        fields = ('solution_description', 'links', 'example_code', "solution_privacy")


class ContentForm(forms.ModelForm):
    class Meta:
        model = Content
        fields = ('problem_description', 'example_input', 'example_output',)


class ProblemForm(forms.ModelForm):
    class Meta:
        model = Problem
        exclude = ('created_by', 'content', 'solution', 'categories', 'forked_from',)


class CategoriesForm(forms.Form):
    categories = forms.CharField(max_length=1000)


class ChallengeForm(forms.ModelForm):
    class Meta:
        model = Challenge
        exclude = ('problems',)


class PDFForm(forms.Form):
    problem = forms.FileField()
    solution = forms.FileField()

    def clean(self):
        form_data = self.cleaned_data
        if form_data['problem'] == None:
            pass
        if form_data['solution'] == None:
            pass
        return form_data

#default complexities
Category.objects.get_or_create(name="o(n!)", type="complexity")
Category.objects.get_or_create(name="o(2^n)", type="complexity")
Category.objects.get_or_create(name='o(n^2)', type="complexity")
Category.objects.get_or_create(name='o(nlogn)', type="complexity")
Category.objects.get_or_create(name='o(n)', type="complexity")
Category.objects.get_or_create(name='o(logn)', type="complexity")
Category.objects.get_or_create(name='o(1)', type="complexity")
#default data structures
Category.objects.get_or_create(name='stack', type="data-structure")
Category.objects.get_or_create(name='queue', type="data-structure")
Category.objects.get_or_create(name='dictionary', type="data-structure")
Category.objects.get_or_create(name='binary-search-tree', type="data-structure")
Category.objects.get_or_create(name='priority-queue', type="data-structure")
Category.objects.get_or_create(name='hashing', type="data-structure")
Category.objects.get_or_create(name='strings', type="data-structure")
Category.objects.get_or_create(name='suffix-tree', type="data-structure")
Category.objects.get_or_create(name='arrays', type="data-structure")
Category.objects.get_or_create(name='graphs', type="data-structure")
Category.objects.get_or_create(name='sets', type="data-structure")
Category.objects.get_or_create(name='kd-trees', type="data-structure")
#default paradigms
Category.objects.get_or_create(name='sorting', type="paradigm")
Category.objects.get_or_create(name='searching', type="paradigm")
Category.objects.get_or_create(name='shortest-path', type="paradigm")
Category.objects.get_or_create(name='approximate-string-matching', type="paradigm")
Category.objects.get_or_create(name='longest-increasing-sequence', type="paradigm")
Category.objects.get_or_create(name='longest-increasing-sequence', type="paradigm")
Category.objects.get_or_create(name='linear-equations', type="paradigm")
Category.objects.get_or_create(name='bandwidth-reduction', type="paradigm")
Category.objects.get_or_create(name='matrix-multiplication', type="paradigm")
Category.objects.get_or_create(name='determinants', type="paradigm")
Category.objects.get_or_create(name='permanents', type="paradigm")
Category.objects.get_or_create(name='constrained-optimisation', type="paradigm")
Category.objects.get_or_create(name='unconstrained-optimisation', type="paradigm")
Category.objects.get_or_create(name='linear-programming', type="paradigm")
Category.objects.get_or_create(name='random-number-generation', type="paradigm")
Category.objects.get_or_create(name='factoring', type="paradigm")
Category.objects.get_or_create(name='primality-testing', type="paradigm")
Category.objects.get_or_create(name='arbitrary-precision-arithmetic', type="paradigm")
Category.objects.get_or_create(name='discrete-fourier-transform', type="paradigm")
Category.objects.get_or_create(name='median', type="paradigm")
Category.objects.get_or_create(name='selection', type="paradigm")
Category.objects.get_or_create(name='generating-permutations', type="paradigm")
Category.objects.get_or_create(name='generating-subsets', type="paradigm")
Category.objects.get_or_create(name='generating-partitions', type="paradigm")
Category.objects.get_or_create(name='generating-graphs', type="paradigm")
Category.objects.get_or_create(name='topological-sorting', type="paradigm")
Category.objects.get_or_create(name='minimum-spanning-tree', type="paradigm")
Category.objects.get_or_create(name='transitive-closure', type="paradigm")
Category.objects.get_or_create(name='transitive-reduction', type="paradigm")
Category.objects.get_or_create(name='matching', type="paradigm")
Category.objects.get_or_create(name='eulerian-cycle', type="paradigm")
Category.objects.get_or_create(name='chinese-postman', type="paradigm")
Category.objects.get_or_create(name='edge-connectivity', type="paradigm")
Category.objects.get_or_create(name='vertex-connectivity', type="paradigm")
Category.objects.get_or_create(name='network-flow', type="paradigm")
Category.objects.get_or_create(name='planarity-detection', type="paradigm")
Category.objects.get_or_create(name='planarity-embedding', type="paradigm")
Category.objects.get_or_create(name='clique', type="paradigm")
Category.objects.get_or_create(name='independent-set', type="paradigm")
Category.objects.get_or_create(name='vertex-cover', type="paradigm")
Category.objects.get_or_create(name='travelling-salesman', type="paradigm")
Category.objects.get_or_create(name='hamiltonian-cycle', type="paradigm")
Category.objects.get_or_create(name='graph-partition', type="paradigm")
Category.objects.get_or_create(name='vertex-colouring', type="paradigm")
Category.objects.get_or_create(name='edge-colouring', type="paradigm")
Category.objects.get_or_create(name='graph-isomorphism', type="paradigm")
Category.objects.get_or_create(name='steiner-tree', type="paradigm")
Category.objects.get_or_create(name='feedback-edge', type="paradigm")
Category.objects.get_or_create(name='vertext-set', type="paradigm")
Category.objects.get_or_create(name='robust-geometric-primitives', type="paradigm")
Category.objects.get_or_create(name='convex-hull', type="paradigm")
Category.objects.get_or_create(name='triangulation', type="paradigm")
Category.objects.get_or_create(name='voronoi-diagrams', type="paradigm")
Category.objects.get_or_create(name='nearest-neighbour-search', type="paradigm")
Category.objects.get_or_create(name='range-search', type="paradigm")
Category.objects.get_or_create(name='point-location', type="paradigm")
Category.objects.get_or_create(name='intersection-diagram', type="paradigm")
Category.objects.get_or_create(name='bin-packing', type="paradigm")
Category.objects.get_or_create(name='medial-axis-transform', type="paradigm")
Category.objects.get_or_create(name='polygon-partitioning', type="paradigm")
Category.objects.get_or_create(name='simplifying-polygons', type="paradigm")
Category.objects.get_or_create(name='shape-similarity', type="paradigm")
Category.objects.get_or_create(name='motion-planning', type="paradigm")
Category.objects.get_or_create(name='maintaining-line-arrangements', type="paradigm")
Category.objects.get_or_create(name='minkowski-sum', type="paradigm")
Category.objects.get_or_create(name='set-cover', type="paradigm")
Category.objects.get_or_create(name='set-packing', type="paradigm")
Category.objects.get_or_create(name='string-matching', type="paradigm")
Category.objects.get_or_create(name='text-compression', type="paradigm")
Category.objects.get_or_create(name='cryptography', type="paradigm")
Category.objects.get_or_create(name='finite-state-machine-minimisation', type="paradigm")
Category.objects.get_or_create(name='longest-common-substring', type="paradigm")
Category.objects.get_or_create(name='shortest-common-superstring', type="paradigm")
#default algorithms
Category.objects.get_or_create(name='heapsort', type="algorithm")
Category.objects.get_or_create(name='mergesort', type="algorithm")
Category.objects.get_or_create(name='quicksort', type="algorithm")
Category.objects.get_or_create(name='bucketing', type="algorithm")
Category.objects.get_or_create(name='binary-search', type="algorithm")
Category.objects.get_or_create(name='divide-and-conquer', type="algorithm")
Category.objects.get_or_create(name='breadth-first-search', type="algorithm")
Category.objects.get_or_create(name='depth-first-search', type="algorithm")
Category.objects.get_or_create(name='backtracking', type="algorithm")
Category.objects.get_or_create(name='search-pruning', type="algorithm")

