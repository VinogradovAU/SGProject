from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm

from authapp.models import HubUser, HubUserProfile


class HubUserLoginForm(AuthenticationForm):
    class Meta:
        model = HubUser
        fields = ('username', 'password')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'


class HubUserRegisterForm(UserCreationForm):
    password1 = forms.CharField(max_length=16, widget=forms.PasswordInput(
        attrs={'placeholder': 'Пароль'}))
    password2 = forms.CharField(max_length=16, widget=forms.PasswordInput(
        attrs={'placeholder': 'Пароль еще раз'}))

    email = forms.CharField(max_length=100, required=True)

    widgets = {
        'email': forms.EmailInput(attrs={'required': True})
    }

    class Meta:
        model = HubUser
        fields = ('username', 'password1', 'password2', 'email')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'
            field.help_text = ''

    def clean_email(self):
        email = self.cleaned_data['email']
        if email and HubUser.objects.filter(email=email).exists():
            raise forms.ValidationError('такой email уже зарегистрирован')
        return email


class HubUserUpdateForm(forms.ModelForm):
    class Meta:
        model = HubUser
        fields = ('username', 'avatar', 'age',)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'
            field.help_text = ''


class HubUserProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = HubUserProfile
        fields = ('name', 'specialization', 'sex', 'birthdate', 'location', 'location_city',)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'
            field.help_text = ''
            if field_name == 'birthdate':
                field.widget = forms.widgets.DateInput(attrs={'type': 'date', 'class': 'form-control'},
                                                       format='%Y-%m-%d')



