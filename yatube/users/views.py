from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.generic import CreateView

from .forms import CreationForm


class SignUp(CreateView):
    form_class = CreationForm
    success_url = reverse_lazy("posts:index")
    template_name = "users/signup.html"


def password_change(request):
    return render(request, "users/password_change_form.html")
