from django.shortcuts import render
from django.http import HttpResponse
from django.views.generic import View

class Index(View):
     def get(self, request):
        return render(request, 'problems/index.html')
