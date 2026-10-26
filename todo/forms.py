from django import forms
from django.forms import ModelForm
from .models import TodoList, UserProfile
from django.contrib.auth.models import User


class TodoForm(ModelForm):
    class Meta:
        model = TodoList
        fields = ['title', 'priority', 'description', 'due_date', 'status']

        labels = {
            'title': 'عنوان',
            'priority': 'اولویت',
            'description': 'توضیحات',
            'due_date': 'تاریخ انجام',
            'status': 'وضعیت',
        }

        widgets = {
            'title': forms.TextInput(attrs={
                'placeholder': 'مثلاً: آماده‌سازی گزارش ماهانه',
            }),
            'description': forms.Textarea(attrs={
                'rows': 5,
                'placeholder': 'جزئیات وظیفه، اهداف و نکات مهم را اینجا بنویسید...',
            }),
            'due_date': forms.DateTimeInput(
                attrs={'type': 'datetime-local'},
                format='%Y-%m-%dT%H:%M',
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['due_date'].input_formats = ['%Y-%m-%dT%H:%M']


class UserProfileForm(ModelForm):
    class Meta:
        model = UserProfile
        fields = ['profile_image', 'email', 'organizational_email', 'mobile', 'internal_number', 'bio']
        labels = {
            'profile_image': 'عکس پروفایل',
            'email': 'ایمیل',
            'organizational_email': 'ایمیل سازمانی',
            'mobile': 'موبایل',
            'internal_number': 'داخلی',
            'bio': 'درباره من',
        }


class UserForm(ModelForm):
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name']
        labels = {
            'username': 'نام کاربری',
            'first_name': 'نام',
            'last_name': 'نام خانوادگی',
        }