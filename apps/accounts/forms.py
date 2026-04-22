"""
Формы модуля авторизации.
"""
from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import User


class PatientRegistrationForm(UserCreationForm):
    """Форма регистрации нового пациента."""

    email = forms.EmailField(
        required=True,
        label='Email',
        widget=forms.EmailInput(attrs={'placeholder': 'example@mail.ru'}),
    )
    first_name = forms.CharField(
        required=True,
        label='Имя',
        max_length=150,
    )
    last_name = forms.CharField(
        required=True,
        label='Фамилия',
        max_length=150,
    )
    phone = forms.CharField(
        required=False,
        label='Телефон',
        max_length=20,
        widget=forms.TextInput(attrs={'placeholder': '+7 (999) 000-00-00'}),
    )
    pd_consent = forms.BooleanField(
        required=True,
        label='Я даю согласие на обработку персональных данных (ФЗ-152)',
    )

    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'phone',
                  'password1', 'password2', 'pd_consent')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = User.Role.PATIENT
        user.email = self.cleaned_data['email']
        user.phone = self.cleaned_data.get('phone', '')
        user.pd_consent = self.cleaned_data['pd_consent']
        if commit:
            user.save()
        return user


class LoginForm(AuthenticationForm):
    """Кастомная форма входа с Bootstrap-стилями."""

    username = forms.CharField(
        label='Логин или Email',
        widget=forms.TextInput(attrs={'autofocus': True}),
    )
    password = forms.CharField(
        label='Пароль',
        widget=forms.PasswordInput(),
    )


class ProfileUpdateForm(forms.ModelForm):
    """Форма редактирования профиля пациента."""

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email', 'phone')
        labels = {
            'first_name': 'Имя',
            'last_name': 'Фамилия',
            'email': 'Email',
            'phone': 'Телефон',
        }
