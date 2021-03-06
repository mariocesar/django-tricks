from uuid import uuid4

from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _

from .mixins import MPAwareModel

treebeard = True

try:
    from treebeard.mp_tree import MP_Node
except ImportError:
    treebeard = False


class UniqueTokenModel(models.Model):
    token = models.CharField(max_length=32, unique=True, blank=True)

    class Meta:
        abstract = True

    def get_token(self):
        return str(uuid4().hex)

    def save(self, **kwargs):
        if not self.token:
            self.token = self.get_token()
        super().save(**kwargs)


if treebeard:
    class MaterializedPathNode(MPAwareModel, MP_Node):
        slug = models.SlugField(max_length=255, db_index=True, unique=False, blank=True)
        node_order_by = ['name']
        node_order_by = ['numval', 'strval']

        class Meta:
            abstract = True


class MutableModelManager(models.QuerySet):
    def by_type(self, model_class):
        return self.filter(specific_type=ContentType.objects.get_for_model(model_class))


class MutableModel(models.Model):
    """A Model that if inherited from will store the specific class reference in self."""

    specific_type = models.ForeignKey(
        ContentType,
        verbose_name=_('specific type'),
        related_name='+',
        editable=False,
        on_delete=models.PROTECT)

    class Meta:
        abstract = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.pk and not self.specific_type_id:
            # this model is being newly created rather than retrieved from the db;
            # set content type to correctly represent the model class that this was
            # created as
            self.specific_type = ContentType.objects.get_for_model(self)

    @cached_property
    def specific(self):
        """Return this page in its most specific subclassed form."""

        specific_type = ContentType.objects.get_for_id(self.specific_type_id)
        model_class = specific_type.model_class()
        if model_class is None:
            return self
        elif isinstance(self, model_class):
            return self
        else:
            return specific_type.get_object_for_this_type(id=self.id)

    @cached_property
    def specific_class(self):
        """Return the class that this page would be if instantiated in its most specific form."""

        specific_type = ContentType.objects.get_for_id(self.specific_type_id)
        return specific_type.model_class()
