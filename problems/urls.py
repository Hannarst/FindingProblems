from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^$', views.Index.as_view(), name='index'),
    url(r'^add/?$', views.AddProblem.as_view(), name="add_problem"),
    url(r'^edit/(?P<problem_id>[0-9]+)?$', views.EditProblem.as_view(), name="edit_problem"),
    url(r'^fork/(?P<problem_id>[0-9]+)?$', views.ForkProblem.as_view(), name="fork_problem"),
    url(r'^view/(?P<problem_id>[0-9]+)/?$', views.ViewProblem.as_view(), name="view_problem"),
    url(r'^challenges/add/?$', views.AddChallenge.as_view(), name="add_challenge"),
    url(r'^challenges/?$', views.ChallengeIndex.as_view(), name="challenge_index"),
    url(r'^challenges/(?P<challenge_id>[0-9]+)/?$', views.ViewChallenge.as_view(), name="view_challenge"),
    url(r'^challenges/edit/(?P<challenge_id>[0-9]+)?$', views.EditChallenge.as_view(), name="edit_challenge"),
]
