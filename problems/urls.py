from django.conf.urls import url
from django.contrib.auth import views as auth_views
from . import views

from forms import LoginForm

urlpatterns = [
    url(r'^$', views.Index.as_view(), name='index'),
    url(r'^add/?$', views.AddProblem.as_view(), name="add_problem"),
    url(r'^edit/(?P<problem_id>[0-9]+)?$', views.EditProblem.as_view(), name="edit_problem"),
    url(r'^fork/(?P<problem_id>[0-9]+)?$', views.ForkProblem.as_view(), name="fork_problem"),
    url(r'^view/(?P<problem_id>[0-9]+)/?$', views.ViewProblem.as_view(), name="view_problem"),
    url(r'^accounts/create_account/?$', views.CreateAccount.as_view(), name="create_account"),
    url(r'^accounts/activate/?$', views.ActivateAccount.as_view(), name="activate"),
    url(r'^accounts/login/?$', auth_views.login, {'template_name': 'login.html', 'authentication_form': LoginForm}, name="login"),
    url(r'^accounts/logout/?$', auth_views.logout_then_login, name="logout"),
    url(r'^accounts/password/reset/?$', auth_views.password_reset, name="password_reset"),
    url(r'^accounts/password/reset/done/?$', auth_views.password_reset_done, name="password_done"),
    url(r'^accounts/password/reset/confirm/?$', auth_views.password_reset_confirm, name="password_reset_confirm"),
    url(r'^accounts/password/reset/success/?$', auth_views.password_reset_complete, name="password_reset_success"),
    url(r'^accounts/password/change/?$', auth_views.password_change, name="password_change"),
    url(r'^accounts/password/change/done/?$', auth_views.password_change_done, name="password_change_done"),
    url(r'^challenges/?$', views.ChallengeIndex.as_view(), name="challenge_index"),
    url(r'^challenges/add/?$', views.AddChallenge.as_view(), name="add_challenge"),
    url(r'^challenges/(?P<challenge_id>[0-9]+)/?$', views.ViewChallenge.as_view(), name="view_challenge"),
    url(r'^challenges/(?P<challenge_id>[0-9]+)/add/(?P<problem_id>[0-9]+)/?$', views.AddToChallenge.as_view(), name="add_to_challenge"),
    url(r'^challenges/(?P<challenge_id>[0-9]+)/remove/(?P<problem_id>[0-9]+)/?$', views.RemoveFromChallenge.as_view(), name="remove_from_challenge"),

]
