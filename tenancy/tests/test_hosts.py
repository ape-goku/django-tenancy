from __future__ import unicode_literals

import sys
# TODO: Remove when support for Python 2.6 is dropped
if sys.version_info >= (2, 7):
    from unittest import skipIf, skipUnless
else:
    from django.utils.unittest import skipIf, skipUnless

from django.core.exceptions import ImproperlyConfigured
from django.test.utils import override_settings
from django.utils.encoding import force_bytes

from ..middleware import TenantHostMiddleware
from ..models import Tenant

from .utils import TenancyTestCase


try:
    import django_hosts
except ImportError:
    django_hosts = None


def django_hosts_installed_setup(func):
    func = override_settings(
        DEFAULT_HOST='default',
        ROOT_HOSTCONF='tenancy.tests.hosts',
        MIDDLEWARE_CLASSES=(
            'django_hosts.middleware.HostsMiddleware',
            'tenancy.middleware.TenantHostMiddleware'
        )
    )(func)
    return skipUnless(
        django_hosts,
        'django-hosts is not installed.'
    )(func)


@override_settings(ROOT_URLCONF='tenancy.tests.urls')
class TenantHostMiddlewareTest(TenancyTestCase):
    @classmethod
    def tenant_client(cls, tenant):
        domain = "%s.testserver" % tenant.name
        return cls.client_class(SERVER_NAME=domain)

    @skipIf(django_hosts, 'django-hosts is installed.')
    def test_not_installed(self):
        self.assertRaisesMessage(
            ImproperlyConfigured,
            'You must install django-hosts in order to use '
            '`TenantHostMiddleware`.',
            TenantHostMiddleware
        )

    @skipUnless(django_hosts, 'django-hosts is not installed.')
    @override_settings(
        MIDDLEWARE_CLASSES=(
            'tenancy.middleware.TenantHostMiddleware',
            'django_hosts.middleware.HostsMiddleware'
        )
    )
    def test_wrong_order(self):
        self.assertRaisesMessage(
            ImproperlyConfigured,
            "Make sure that 'django_hosts.middleware.HostsMiddleware' is "
            "placed before 'tenancy.middleware.TenantHostMiddleware' in your "
            "`MIDDLEWARE_CLASSES` setting.",
            TenantHostMiddleware
        )

    @django_hosts_installed_setup
    def test_tenant_not_found(self):
        tenant = Tenant(name='inexistent')
        client = self.tenant_client(tenant)
        response = client.get('/')
        self.assertEqual(response.status_code, 404)

    @django_hosts_installed_setup
    def test_tenant_found(self):
        client = self.tenant_client(self.tenant)
        response = client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, force_bytes(self.tenant.name))
