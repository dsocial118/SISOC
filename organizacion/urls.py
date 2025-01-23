from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LogoutView
from django.urls import path

from usuarios.forms import MySetPasswordFormm
from usuarios.views import (

)

urlpatterns = []