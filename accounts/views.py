import time
import uuid
from random import randint

import pyotp
from django import views
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import User
from django.core.mail import EmailMultiAlternatives
from django.http import JsonResponse
from django.shortcuts import render, redirect

# Create your views here.
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.generic import ListView, CreateView, UpdateView, DeleteView

from accounts.auth_helper import is_user_admin
from accounts.forms import LoginForm, UserForm, UserProfileForm, UpdateAdminForm, OtpForm, UserPasswordForm, \
    LocationForm
from accounts.models import UserProfile, JitsiUser, VerificationCode, Location
from restrictions.forms import RestrictionFormWithoutUserForm
from restrictions.models import Restrictions
from room.models import Room
from utils.helpers import get_obj, split_name


def login_view(request):
    form = LoginForm()
    return render(request, "login.html", {"form": form})

class EmailVerificationMixin(object):
    from_email = 'voipxmeet@voipxint.com'
    subject = 'Action required'
    default_host = 'talk.gomeeting.org'

    @staticmethod
    def create_code(user):
        try:
            # verification_code = str(uuid.uuid4())
            verification_code = str(randint(100000, 999999))
            VerificationCode.objects.create(
                user=user,
                email=user.email,
                code=verification_code
            )
            return verification_code
        except Exception as e:
            print(e)
            return None

    def send_mail(self, content, mail_to):
        try:
            msg = EmailMultiAlternatives(self.subject, content, self.from_email, [mail_to])
            msg.attach_alternative(content, "text/html")
            msg.send()
            return True
        except Exception as e:
            return False

    def verify_code(self, user, code):
        return VerificationCode.objects.filter(
            user=user,
            code=code,
            email=user.email
        ).exists()

    def send_verification_email(self, user, verification_host=None):
        verification_code = self.create_code(user)
        html_content = 'Use this code to verify your email: %s <br> ' % verification_code
        html_content += '<br><p>This code is valid for 48 hours</p><br><br>'
        html_content += 'Thanks for staying with talk.gomeeting.org'
        self.send_mail(html_content, user.email)
        return True


class RegisterView(View):
    form = UserForm
    profile_form = UserProfileForm
    template = "register.html"

    def get(self, request, *args, **kwargs):
        form = self.form()
        profile_form = self.profile_form()
        return render(request, self.template, locals())

    def post(self, request, *args, **kwargs):
        form = self.form(request.POST)
        profile_form = self.profile_form(request.POST)
        if form.is_valid() and profile_form.is_valid():
            user = form.save(commit=False)
            user.password = make_password(form.cleaned_data.get('password'))
            user.first_name, user.last_name = split_name(profile_form.cleaned_data.get('name'))
            user.is_active = False
            user.save()

            user_profile = profile_form.save(commit=False)
            user_profile.user_uid = uuid.uuid4()
            user_profile.user = user
            user_profile.user_type = UserProfile.ADMIN
            user_profile.save()

            Restrictions.objects.create(
                user=user,
                max_member_count=-1,
                max_room_count=-1,
                max_time_length=-1
            )

            return redirect(reverse("accounts:login"))
        return render(request, self.template, locals())


@method_decorator(login_required, name='dispatch')
class CreateUserView(View):
    form = UserForm
    profile_form = UserProfileForm
    # restriction_form = RestrictionFormWithoutUserForm
    template = 'create_creator.html'

    def get(self, request, *args, **kwargs):
        form = self.form()
        profile_form = self.profile_form()
        # restriction_form = self.restriction_form()
        return render(request, self.template, locals())

    def post(self, request, *args, **kwargs):
        form = self.form(request.POST)
        profile_form = self.profile_form(request.POST)
        profile_form.fields['city'].queryset = Location.objects.filter(id=request.POST.get('city'))
        # restriction_form = self.restriction_form(request.POST)
        if form.is_valid() and profile_form.is_valid():
            user = form.save(commit=False)
            user.password = make_password(form.cleaned_data.get('password'))
            user.first_name, user.last_name = split_name(profile_form.cleaned_data.get('name'))
            user.save()

            user_profile = profile_form.save(commit=False)
            user_profile.user_uid = uuid.uuid4()
            user_profile.user = user
            user_profile.user_type = UserProfile.SALES_PERSON
            user_profile.user_city = profile_form.cleaned_data.get('city')
            user_profile.user_state = profile_form.cleaned_data.get('state')
            user_profile.save()

            restriction = Restrictions.objects.create(
                user=user,
                max_time_length=-1,
                max_room_count=1,
                max_member_count=2
            )
            restriction.user = user
            restriction.save()

            Room.objects.create(
                name='Customer care',
                room_id=str(int(time.time())*1000),
                room_type=Room.PUBLIC,
                created_by=user,
                max_number_of_user=2,
                max_length=-1,
                start_time=int(time.time()*1000)
            )

            return redirect(reverse("accounts:dashboard"))
        return render(request, self.template, locals())

@method_decorator(login_required, name='dispatch')
class DeleteUserView(View):
    def get(self, request, *args, **kwargs):
        user_id = kwargs.get('pk')
        user = JitsiUser.objects.get(id=user_id)
        if user.profile.user_type == UserProfile.ADMIN:
            if request.user.is_staff and request.user.profile.user_type == UserProfile.ADMIN and request.user.is_superuser:
                user.delete()
                return redirect(reverse("accounts:dashboard"))
        elif user.profile.user_type == UserProfile.SALES_PERSON and request.user.profile.user_type == UserProfile.ADMIN:
            user.delete()
            return redirect(reverse("accounts:dashboard"))


class UpdateUserPassword(View):
    form = UserPasswordForm
    def get(self, request, *args, **kwargs):
        if request.user.is_staff and request.user.profile.user_type == UserProfile.ADMIN and request.user.is_superuser:
            user_id = kwargs.get('pk')
            update_user = JitsiUser.objects.get(id=user_id)
            form = self.form()
            return render(request, 'update_user_password.html', locals() )
    def post(self, request, *args, **kwargs):
        if request.user.is_staff and request.user.profile.user_type == UserProfile.ADMIN and request.user.is_superuser:
            form = self.form(request.POST)
            user_id = kwargs.get('pk')
            update_user = JitsiUser.objects.get(id=user_id)
            if form.is_valid():
                update_user.set_password(form.cleaned_data['password'])
                update_user.save()
                return redirect(reverse('accounts:dashboard'))
            return render(request, 'update_user_password.html', locals())

@method_decorator(login_required, name='dispatch')
class VerifyOtpView(View, EmailVerificationMixin):
    template='otp.html'
    form = OtpForm

    def get(self, request):
        self.send_verification_email(request.user)
        form = self.form()
        return render(request, self.template, locals())

    def post(self, request):
        form = self.form(data=request.POST)
        if form.is_valid():
            code = form.cleaned_data.get('otp')
            if self.verify_code(request.user, code):
                request.session['email_verified'] = True

                return redirect(reverse('accounts:dashboard'))
            form.add_error("otp", "Your otp is worng")
        return render(request, self.template, locals())



@method_decorator(login_required, name='dispatch')
class CreateAdminView(View):
    form = UserForm
    profile_form = UserProfileForm
    template = 'create_admin.html'

    def get(self, request, *args, **kwargs):
        form = self.form()
        profile_form = self.profile_form()
        return render(request, self.template, locals())

    def post(self, request, *args, **kwargs):
        form = self.form(request.POST)
        profile_form = self.profile_form(request.POST)
        if form.is_valid() and profile_form.is_valid():
            user = form.save(commit=False)
            user.password = make_password(form.cleaned_data.get('password'))
            user.first_name, user.last_name = split_name(profile_form.cleaned_data.get('name'))
            user.save()

            user_profile = profile_form.save(commit=False)
            user_profile.user_uid = uuid.uuid4()
            user_profile.user = user
            user_profile.user_type = UserProfile.ADMIN
            user_profile.save()

            Restrictions.objects.create(
                user=user,
                max_member_count=-1,
                max_room_count=-1,
                max_time_length=-1
            )

            return redirect(reverse("accounts:dashboard"))
        return render(request, self.template, locals())

@method_decorator(login_required, name='dispatch')
class LocationCreateView(CreateView):
    form_class = LocationForm
    template_name = 'location_create.html'
    success_url = '/locations/'

@method_decorator(login_required, name='dispatch')
class LocationListView(ListView):
    model = Location
    template_name = 'location_list.html'

@method_decorator(login_required, name='dispatch')
class LocationUpdateView(UpdateView):
    model = Location
    form_class = LocationForm
    template_name = 'location_create.html'
    success_url = '/locations/'

    def get_object(self, queryset=None, *args, **kwargs):
        loc_id = self.kwargs.get('pk')
        return Location.objects.get(id=loc_id)


@method_decorator(login_required, name='dispatch')
class LocationDeleteView(DeleteView):
    model = Location
    success_url = '/locations/'
    template_name = 'location_delete.html'

    def get_object(self, queryset=None):
        loc_id = self.kwargs.get('pk')
        return Location.objects.get(id=loc_id)

class LocationApiView(View):
    def get(self, request):
        loc_id = request.GET.get('loc_id')
        loc_type = request.GET.get('loc_type')

        location = Location.objects.get(id = loc_id)
        children_locs = location.get_childs_by_type(loc_type)
        result = []
        for l in children_locs:
            result.append({
                "id": l.id,
                "text": str(l)
            })
        return JsonResponse(data=result, safe=False)

@method_decorator(login_required, name='dispatch')
class AdminListView(ListView):
    model = UserProfile
    template_name = 'admin_list.html'

    def get_queryset(self):
        if self.request.user.is_superuser:
            return UserProfile.objects.filter(user_type=UserProfile.ADMIN)
        elif self.request.user.is_staff:
            return UserProfile.objects.filter(user_type=UserProfile.ADMIN, user__is_superuser=False)
        return UserProfile.objects.filter(user_type=UserProfile.ADMIN, user__is_superuser=False, user__is_staff=False)



@method_decorator(login_required, name='dispatch')
class AdminUpdateView(View):
    form = UpdateAdminForm
    template_name = 'update_admin.html'

    def get(self, request, *args, **kwargs):
        admin_id = kwargs.get('pk')
        admin_user = JitsiUser.objects.get(pk=admin_id, profile__user_type=UserProfile.ADMIN)
        form = self.form(instance=admin_user)
        return render(request, self.template_name, locals())

    def post(self, request, *args, **kwargs):
        admin_id = kwargs.get('pk')
        admin_user = JitsiUser.objects.get(pk=admin_id, profile__user_type=UserProfile.ADMIN)
        form = self.form(request.POST, instance=admin_user)
        if form.is_valid():
            form.save()
            return  redirect(reverse('accounts:admin_list'))
        return render(request, self.template_name, locals())


def login_submit(request):
    if request.POST:
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')

            user = authenticate(username=username, password=password)
            email_user = get_obj(User, email=username)
            if user and getattr(user, 'is_active', False):
                login(request, user)
                if 'next' in request.GET:
                    return redirect(request.GET.get('next', '/'))
                # if user.profile.user_type == UserProfile.SALES_PERSON:
                return redirect(reverse('accounts:dashboard'))
                # return redirect(reverse('accounts:verify-otp'))
            elif email_user and getattr(email_user, 'is_active', False):
                user = authenticate(username=email_user.username, password=password)
                if user:
                    login(request, user)

                    # if user.profile.user_type == UserProfile.SALES_PERSON:
                    return redirect(reverse('accounts:dashboard'))
                    if 'next' in request.GET:
                        return redirect(request.GET.get('next', '/'))
                    # return redirect(reverse('accounts:dashboard'))
                    # return redirect(reverse('accounts:verify-otp'))
            return render(request, "login.html", {"form": form, 'errors': "You have entered wrong username/email or password"})
        return render(request, "login.html", {"form": form, 'errors': form.errors})
    return redirect(reverse("accounts:login"))

def logout_view(request):
    rooms = Room.objects.filter(created_by=request.user)
    for r in rooms:
        r.room_status = Room.OFFLINE
        r.save()
    logout(request)
    return redirect(reverse("accounts:login"))

@login_required
def dashboard(request):
    return render(request, 'dashboard.html', {})