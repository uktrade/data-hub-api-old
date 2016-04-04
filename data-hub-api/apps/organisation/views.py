from django.contrib import messages
from django.views.generic import ListView
from django.views.generic.edit import CreateView, UpdateView

from reversion import revisions as reversion

from .models import Organisation


class OrganisationMixin(object):
    model = Organisation
    context_object_name = 'organisation'


class Index(OrganisationMixin, ListView):
    context_object_name = 'organisations'

    def get_q(self):
        return self.request.GET.get('q')

    def get_queryset(self):
        q = self.get_q()

        if not q:
            return self.model.objects.none()

        return self.model.objects.filter(name__icontains=q)

    def get_context_data(self, **kwargs):
        context_data = super(Index, self).get_context_data(**kwargs)
        context_data['q'] = self.get_q()
        return context_data


class Create(OrganisationMixin, CreateView):
    fields = [
        'name', 'alias',
        'uk_organisation', 'country',
        'postcode', 'address1', 'city', 'uk_region',
        'country_code', 'area_code', 'phone_number',
        'email_address', 'sector'
    ]

    def form_valid(self, form):
        messages.info(self.request, 'Organisation saved.')
        return super(Update, self).form_valid(form)


class Update(OrganisationMixin, UpdateView):
    fields = [
        'name', 'alias',
        'uk_organisation', 'country',
        'postcode', 'address1', 'city', 'uk_region',
        'country_code', 'area_code', 'phone_number',
        'email_address', 'sector'
    ]

    def form_valid(self, form):
        messages.info(self.request, 'Organisation saved.')
        return super(Update, self).form_valid(form)

    def get_context_data(self, **kwargs):
        context_data = super(Update, self).get_context_data(**kwargs)
        context_data.update({
            'versions': reversion.get_for_object(self.object)
        })
        return context_data
