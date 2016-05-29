from django.core.exceptions import ImproperlyConfigured
from django.http import Http404
from django.utils.translation import gettext_lazy as _
from django.views.generic.base import TemplateResponseMixin, View
from django.views.generic.detail import SingleObjectMixin
from django.views.generic.list import MultipleObjectMixin


class MasterDetailMixin(MultipleObjectMixin, SingleObjectMixin):
    belongs_model = None
    belongs_queryset = None
    related_name = None

    def get_object(self, queryset=None):
        queryset = self.get_belongs_queryset()
        return super(MultipleObjectMixin, self).get_object(queryset=queryset)

    def get_related_name(self):
        if self.related_name:
            return self.related_name

    def get_belongs_queryset(self):
        queryset = self.belongs_queryset

        if queryset is None:
            if self.belongs_model:
                queryset = self.belongs_model._default_manager.all()
            else:
                raise ImproperlyConfigured(
                    "%(cls)s is missing the Belongs QuerySet. Define "
                    "%(cls)s.model, %(cls)s.belongs_queryset, or override "
                    "%(cls)s.get_belongs_queryset()." % {'cls': self.__class__.__name__})

        return queryset.all()

    def get_queryset(self, belongs_object=None):
        related_name = self.get_related_name()
        if related_name not in self.belongs_model._meta.fields_map:
            raise ImproperlyConfigured('Wrong related reference')

        return getattr(belongs_object or self.get_object(), related_name).all()


class MasterDetailView(TemplateResponseMixin, MasterDetailMixin, View):
    template_name_suffix = '_list'

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object_list = self.get_queryset(self.object)

        allow_empty = self.get_allow_empty()

        if not allow_empty:
            # When pagination is enabled and object_list is a queryset,
            # it's better to do a cheap query than to load the unpaginated
            # queryset in memory.
            if (self.get_paginate_by(self.object_list) is not None
                and hasattr(self.object_list, 'exists')):
                is_empty = not self.object_list.exists()
            else:
                is_empty = len(self.object_list) == 0
            if is_empty:
                raise Http404(_("Empty list and '%(class_name)s.allow_empty' is False.")
                              % {'class_name': self.__class__.__name__})
        context = self.get_context_data()

        return self.render_to_response(context)

    def get_template_names(self):
        names = super().get_template_names()

        if hasattr(self.object_list, 'model'):
            opts = self.object_list.model._meta
            names.append("%s/%s%s.html" % (opts.app_label, opts.model_name, self.template_name_suffix))

        return names
