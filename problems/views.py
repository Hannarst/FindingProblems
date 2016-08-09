from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.views.generic import View
from models import *
from django.contrib import messages

class Index(View):
     def get(self, request):
        return render(request, 'problems/index.html')

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
