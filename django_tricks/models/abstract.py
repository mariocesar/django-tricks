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

        class Meta:
            abstract = True


class MutableModel(models.Model):
    """A Model that if inherited from will store the specific class reference in self."""
    content_type = models.ForeignKey(
        ContentType,
        verbose_name=_('content type'),
        related_name='+',
        editable=False,
        on_delete=models.PROTECT)

    class Meta:
        abstract = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.id and not self.content_type_id:
            # this model is being newly created rather than retrieved from the db;
            # set content type to correctly represent the model class that this was
            # created as
            self.content_type = ContentType.objects.get_for_model(self)

    @cached_property
    def specific(self):
        """Return this page in its most specific subclassed form."""

        content_type = ContentType.objects.get_for_id(self.content_type_id)
        model_class = content_type.model_class()
        if model_class is None:
            return self
        elif isinstance(self, model_class):
            return self
        else:
            return content_type.get_object_for_this_type(id=self.id)

    @cached_property
    def specific_class(self):
        """Return the class that this page would be if instantiated in its most specific form."""

        content_type = ContentType.objects.get_for_id(self.content_type_id)
        return content_type.model_class()
