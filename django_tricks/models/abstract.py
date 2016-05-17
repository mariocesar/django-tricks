from uuid import uuid4

from django.db import models
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
        return uuid4().hext

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
