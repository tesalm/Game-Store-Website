from django.forms import ModelForm
from .models import Game
from django.contrib.auth.models import User
from django import forms
from django.contrib.auth.forms import UserCreationForm


class GameForm(ModelForm):
    class Meta:
        model = Game
        exclude = ["developer"]


class RegisterForm(UserCreationForm):
    first_name = forms.CharField(max_length=30, required=False, help_text='Optional.')
    last_name = forms.CharField(max_length=30, required=False, help_text='Optional.')
    developer = forms.BooleanField(required=False, help_text='Apply as developer.')
    email = forms.EmailField(max_length=254, required=True, help_text='Required.')
    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'password1', 'password2', 'developer')

