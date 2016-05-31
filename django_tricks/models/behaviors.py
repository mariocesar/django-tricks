from django.db import models


class ComputeFields:
    def contribute_to_class(self, cls, name, virtual_only=True):
        self.model = cls

        def compute_model_fields(sender, **kwargs):
            # Filter editable fields, allow just non-editable fields
            fields = [field for field in iter(sender._meta.local_fields) if not field.editable]

            # Filter fields with an existing compute method
            fields = [field for field in fields if hasattr(sender, 'compute_%s' % field.attname)]

            for field in fields:
                compute_func_field = 'compute_%s' % field.attname
                instance_compute_field = getattr(self.model, compute_func_field)

                # Creates a pre-save signal for each field that will update the value
                def compute_field(**kwargs):
                    instance = kwargs['instance']
                    value = instance_compute_field(instance)
                    setattr(instance, field.attname, value)

                # Updates the receiver method to look like the instance compute field
                compute_field.__module__ = instance_compute_field.__module__
                compute_field.__name__ = instance_compute_field.__name__
                compute_field.__qualname__ = instance_compute_field.__qualname__
                compute_field.__doc__ = instance_compute_field.__doc__
                compute_field.__annotations__ = instance_compute_field.__annotations__

                models.signals.pre_save.connect(
                    compute_field,
                    sender=self.model,
                    weak=False,
                    dispatch_uid=compute_func_field)

        # Make sure it's added when all models are loaded
        models.signals.class_prepared.connect(
            compute_model_fields,
            sender=self.model,
            weak=False,
            dispatch_uid='compute_%s_fields' % self.model._meta.verbose_name)
