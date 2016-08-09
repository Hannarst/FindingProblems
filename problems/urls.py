from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^$', views.Index.as_view(), name='index'),
    url(r'^add/?$', views.AddProblem.as_view(), name="add_problem"),
    url(r'^edit/?$', views.EditProblem.as_view(), name="edit_problem"),
]
