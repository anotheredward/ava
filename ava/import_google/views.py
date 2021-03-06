# flake8: noqa
import os
from django.core.urlresolvers import reverse
from django.shortcuts import get_object_or_404

from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.views.generic.edit import DeleteView

from ava.google_auth.views import retrieve_credential_from_session, django
from ava.import_google.forms import GoogleConfigurationForm
from ava.import_google.google_apps_interface import GoogleDirectoryHelper
from ava.import_google.models import GoogleDirectoryUser, GoogleDirectoryGroup, GoogleConfiguration

# CRUD/Import views for Google Configurations
class GoogleConfigurationIndex(ListView):
    template_name = 'google_apps/GoogleConfiguration_index.html'
    context_object_name = 'google_configuration_list'

    def get_queryset(self):
        return GoogleConfiguration.objects.all()


class GoogleConfigurationDetail(DetailView):
    model = GoogleConfiguration
    context_object_name = 'google_configuration'
    template_name = 'google_apps/GoogleConfiguration_detail.html'


class GoogleConfigurationCreate(CreateView):
    model = GoogleConfiguration
    template_name = 'google_apps/GoogleConfiguration.html'
    form_class = GoogleConfigurationForm


class GoogleConfigurationUpdate(UpdateView):
    model = GoogleConfiguration
    template_name = 'google_apps/GoogleConfiguration.html'
    form_class = GoogleConfigurationForm


class GoogleConfigurationDelete(DeleteView):
    model = GoogleConfiguration
    template_name = 'confirm_delete.html'
    success_url = '/google/'


class GoogleDirectoryUserIndex(ListView):
    model = GoogleDirectoryUser
    template_name = 'google_apps/GoogleDirectoryUser_index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['google_user_list'] = GoogleDirectoryUser.objects.all()
        return context


class GoogleDirectoryUserDetail(DetailView):
    model = GoogleDirectoryUser
    context_object_name = 'googledirectoryuser'
    template_name = 'google_apps/GoogleDirectoryUser_detail.html'


class GoogleDirectoryUserDelete(DeleteView):
    model = GoogleDirectoryUser
    template_name = 'confirm_delete.html'
    success_url = '/google/users/'


class GoogleDirectoryGroupIndex(ListView):
    model = GoogleDirectoryGroup
    template_name = 'google_apps/GoogleDirectoryGroup_index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['google_group_list'] = GoogleDirectoryGroup.objects.all()
        return context


class GoogleDirectoryGroupDetail(DetailView):
    model = GoogleDirectoryGroup
    context_object_name = 'googledirectorygroup'
    template_name = 'google_apps/GoogleDirectoryGroup_detail.html'


class GoogleDirectoryGroupDelete(DeleteView):
    model = GoogleDirectoryGroup
    template_name = 'confirm_delete.html'
    success_url = '/google/groups/'

class GoogleDirectoryImportAuthorisation(django.views.generic.View):

   def get(self, request, pk):
        config_pk = pk
        if config_pk:
            google_config = get_object_or_404(GoogleConfiguration, pk=config_pk)

        if google_config:
            request.session['google_configuration_id'] = google_config.id

        return django.http.HttpResponseRedirect(reverse('google-auth-login-redirect'))

class GoogleDirectoryImport(django.views.generic.View):
    def get(self, request):

        if os.environ.get('USE_MOCK_GOOGLE'):
            credential = "not needed due to local install"
        else:
            credential = retrieve_credential_from_session(request)

        gd_helper = GoogleDirectoryHelper()

        config_pk = self.kwargs.get('pk')
        if config_pk:
            google_config = get_object_or_404(GoogleConfiguration, pk=config_pk)
        else:
            google_config = get_object_or_404(GoogleConfiguration, pk=request.session.get('google_configuration_id'))

        if google_config:
            # import the directory information from google
            import_data = gd_helper.import_google_directory(credential)

            # parse and store the users
            gd_user = GoogleDirectoryUser()
            gd_user.import_from_json(google_config, import_data['users'])

            # parse and store the groups
            gd_group = GoogleDirectoryGroup()
            gd_group.import_from_json(google_config, import_data['groups'], import_data['group_members'])

            self.request.session['google_configuration_id'] = None

        return django.http.HttpResponseRedirect(reverse('know-dashboard'))
