from django.conf.urls import url
from django.contrib.auth import views as auth_views
from django.urls import reverse

from . import views
from FindingProblems.settings import DEFAULT_EMAIL_FROM
from problems.forms import LoginForm

urlpatterns = [
    url(r'^$',
        views.Index.as_view(),
        name='index'),
    url(r'^add/upload/?$',
        views.Upload.as_view(),
        name="upload"),
    url(r'^add/?$',
        views.AddProblem.as_view(),
        name="add_problem"),
    url(r'^edit/(?P<problem_id>[0-9]+)?$',
        views.EditProblem.as_view(),
        name="edit_problem"),
    url(r'^fork/(?P<problem_id>[0-9]+)?$',
        views.ForkProblem.as_view(),
        name="fork_problem"),
    url(r'^view/(?P<problem_id>[0-9]+)/?$',
        views.ViewProblem.as_view(),
        name="view_problem"),
    url(r'^accounts/create_account/?$',
        views.CreateAccount.as_view(),
        name="create_account"),
    url(r'^accounts/activate/?$',
        views.ActivateAccount.as_view(),
        name="activate"),
    url(r'^accounts/login/?$',
        auth_views.login,
        {
            'template_name': 'problems/login.html',
            'authentication_form': LoginForm
        },
        name="login"),
    url(r'^accounts/logout/?$',
        auth_views.logout_then_login,
        name="logout"),
    url(r'^accounts/password/reset/?$',
        auth_views.password_reset,
        {
            'template_name': 'problems/password_reset.html',
            'post_reset_redirect': '/problems/accounts/password/reset/done/',
            'from_email': DEFAULT_EMAIL_FROM,
        },
        name="password_reset"),
    url(r'^accounts/password/reset/done/?$',
        auth_views.password_reset_done,
        {
            'template_name': 'problems/password_reset_done.html'
        },
        name="password_reset_done"),
    url(r'^accounts/password/reset/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/?$',
        auth_views.password_reset_confirm,
        {
            'template_name': 'problems/password_reset_confirm.html',
            'post_reset_redirect': '/problems/accounts/password/complete/'
        },
        name="password_reset_confirm"),
    url(r'^accounts/password/complete/?$',
        auth_views.password_reset_complete,
        {
            'template_name': 'problems/password_reset_complete.html'
        },
        name="password_reset_complete"),
    url(r'^accounts/password/change/?$',
        auth_views.password_change,
        {
            'template_name': 'problems/password_change.html'
        },
        name="password_change"),
    url(r'^accounts/password/change/done/?$',
        auth_views.password_change_done,
        {
            'template_name': 'problems/password_change_done.html'
        },
        name="password_change_done"),
    url(r'^challenges/?$',
        views.ChallengeIndex.as_view(),
        name="challenge_index"),
    url(r'^challenges/add/?$',
        views.AddChallenge.as_view(),
        name="add_challenge"),
    url(r'^challenges/(?P<challenge_id>[0-9]+)/?$',
        views.ViewChallenge.as_view(),
        name="view_challenge"),
    url(r'^challenges/(?P<challenge_id>[0-9]+)/add/(?P<problem_id>[0-9]+)/?$',
        views.AddToChallenge.as_view(),
        name="add_to_challenge"),
    url(r'^challenges/(?P<challenge_id>[0-9]+)/remove/(?P<problem_id>[0-9]+)/?$',
        views.RemoveFromChallenge.as_view(),
        name="remove_from_challenge"),
    url(r'^challenges/quit/?$',
        views.QuitEditingChallenge.as_view(),
        name="quit_editing_challenge"),

]
