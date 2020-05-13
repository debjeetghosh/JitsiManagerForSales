from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect

# Create your views here.
from django.urls import reverse, reverse_lazy
from django.utils.decorators import method_decorator
from django.views import View
from django.views.generic import ListView, UpdateView

from accounts.forms import UserProfileForm
from accounts.models import Location
from restrictions.forms import RestrictionForm
from restrictions.models import Restrictions


@method_decorator(login_required, name="dispatch")
class RestrictionListView(ListView):
    model = Restrictions
    template_name = 'restrictions/list.html'

    def get_queryset(self):
        return self.model.objects.filter(user__is_staff=False, user__is_superuser=False)

@method_decorator(login_required, name="dispatch")
class RestrictionUpdateView(View):
    model = Restrictions
    form_class = RestrictionForm
    profile_form = UserProfileForm
    template_name = 'restrictions/update.html'

    def get(self, request, *args, **kwargs):
        restriction_id = kwargs.get('pk')
        restriction = Restrictions.objects.get(id=restriction_id)
        form = self.form_class(instance=restriction)
        profile_form = self.profile_form(instance=restriction.user.profile)
        profile_form.fields['city'].queryset = Location.objects.filter(id=restriction.user.profile.user_city_id) if restriction.user.profile.user_city else Location.objects.none()
        return render(request=request, template_name=self.template_name, context=locals())

    def post(self, request, *args, **kwargs):
        restriction_id = kwargs.get('pk')
        restriction = Restrictions.objects.get(id=restriction_id)
        form = self.form_class(instance=restriction, data=request.POST)
        profile_form = self.profile_form(instance=restriction.user.profile, data=request.POST)

        profile_form.fields['city'].queryset = Location.objects.filter(id=request.POST.get('city'))
        if form.is_valid() and profile_form.is_valid():
            form.save()
            profile = profile_form.save(commit=False)
            profile.user_state = profile_form.cleaned_data.get('state')
            profile.user_city = profile_form.cleaned_data.get('city')
            profile.save()
            return redirect(reverse('restrictions:restriction_list'))
        return render(request=request, template_name=self.template_name, context=locals())

    def get_object(self, queryset=None):
        return self.model.objects.get(pk=self.kwargs.get('pk'))

    def get_success_url(self):
        return '/restriction/'

