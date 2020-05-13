import pyotp
from django import forms
from django.core.exceptions import NON_FIELD_ERRORS

from accounts.models import UserProfile, JitsiUser, Location


class LoginForm(forms.Form):
    username = forms.CharField(max_length=200, widget=forms.TextInput(attrs={'class': 'form-control'}))
    password = forms.CharField(max_length=200, widget=forms.PasswordInput(attrs={'class': 'form-control'}))


class UpdateAdminForm(forms.ModelForm):
    class Meta:
        model = JitsiUser
        fields = ['is_active', 'is_staff', 'is_superuser']

class LocationForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(LocationForm, self).__init__(*args, **kwargs)
        self.fields['parent_location'].required = False

    class Meta:
        model = Location
        exclude = ('',)
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'location_type': forms.Select(attrs={'class': 'form-control'}),
            'parent_location': forms.Select(attrs={'class': 'form-control'}),
        }
class OtpForm(forms.Form):
    otp = forms.CharField(max_length=200, widget=forms.TextInput(attrs={'class': 'form-control'}))


class UserPasswordForm(forms.Form):
    password = forms.CharField(max_length=200, widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    confirm_password = forms.CharField(max_length=200, widget=forms.PasswordInput(attrs={'class': 'form-control'}))

    def clean(self):
        super().clean()
        clean_data = self.cleaned_data
        password = self.cleaned_data.get('password')
        confirm_password = self.cleaned_data.get('confirm_password')
        if password != confirm_password:
            self.add_error('password', forms.ValidationError("Password and confirm password should match"))


class UserForm(forms.ModelForm):
    class Meta:
        model = JitsiUser
        fields = ['username', 'email', 'password', ]
        error_messages = {
            NON_FIELD_ERRORS: {
                'unique_together': "%(model_name)s's %(field_labels)s are not unique.",
            }
        }

        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.TextInput(attrs={'class': 'form-control'}),
            'password': forms.PasswordInput(attrs={'class': 'form-control'})
        }


class UserProfileForm(forms.ModelForm):
    state = forms.ModelChoiceField(queryset=Location.objects.filter(location_type=Location.STATE), widget=forms.Select(attrs={'class': 'form-control'}))
    city = forms.ModelChoiceField(queryset=Location.objects.none(), widget=forms.Select(attrs={'class': 'form-control'}))

    class Meta:
        model = UserProfile
        fields = [
            'name',
            'state',
            'city',
        ]

        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
        }

