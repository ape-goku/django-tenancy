from __future__ import unicode_literals
import sys

from django.utils.unittest.case import skipIf, skipUnless

from .utils import TenancyTestCase


try:
    from mutant.contrib.boolean.models import NullBooleanFieldDefinition
except ImportError:
    mutant_installed = False
else:
    mutant_installed = True


@skipUnless(mutant_installed, 'django-mutant is not installed.')
@skipIf(sys.version_info < (2, 7), "Model class can't be pickled on python < 2.7")
class MutableTenantModelTest(TenancyTestCase):
    def test_field_creation(self):
        from .models import MutableModel
        model_class = MutableModel.for_tenant(self.tenant)
        model_def = model_class.definition()
        NullBooleanFieldDefinition.objects.create(
            model_def=model_def,
            name='is_cool'
        )
        tenant_mutable_models = self.tenant.mutable_models
        tenant_mutable_models.create(field='test', is_cool=False)
        self.assertEqual(1, tenant_mutable_models.filter(is_cool=False).count())

    def test_subclassing(self):
        from .models import MutableModel, MutableModelSubclass
        model_class = MutableModelSubclass.for_tenant(self.tenant)
        self.assertEqual(
            model_class.non_mutable_fk.field.rel.to,
            self.tenant.specificmodels.model
        )
        model_class.objects.create(
            field='test', non_mutable_fk=self.tenant.specificmodels.create()
        )
        # Add a field to the parent class
        NullBooleanFieldDefinition.objects.create_with_default(False,
            model_def=MutableModel.for_tenant(self.tenant).definition(),
            name='is_cool',
        )
        self.assertEqual(1,
            model_class.objects.filter(field='test', is_cool=False).count()
        )

    def test_ordering(self):
        """
        Ordering is not inherited from an abstract base class thus
        OrderingFieldDefinition must be created in order to maintain the
        specified ordering.
        """
        from .models import MutableModel
        model_class = MutableModel.for_tenant(self.tenant)
        first = model_class.objects.create(field=True)
        second = model_class.objects.create(field=False)
        self.assertQuerysetEqual(
            model_class.objects.values_list('id', flat=True),
            sorted([second.id, first.id], reverse=True),
            int
        )
