from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^$', views.Index.as_view(), name='index'),
    url(r'^add/?$', views.AddProblem.as_view(), name="add_problem")
]
