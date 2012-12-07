# -*- coding: utf-8 -*-

from kobo.hub.models import Arch, Channel

from covscanhub.scan.models import *

from django.contrib.auth.models import User
from django.contrib.auth.models import Permission
from django.test import Client
from django.core.handlers.wsgi import WSGIRequest


__all__ = (
    'fill_db',
    'clear_db',
    'clear_all',
)


def fill_db():
    p1 = Package()
    p1.name = "libssh2"
    p1.blocked = False
    p1.save()
    
    p2 = Package()
    p2.name = "box"
    p2.blocked = False
    p2.save()
    
    p3 = Package()
    p3.name = "kernel"
    p3.blocked = True
    p3.save()

    sr1 = SystemRelease()
    sr1.tag = "rhel-0.1"
    sr1.description = "Red Hat Enterprise Linux 0 release 1"
    sr1.active = True
    sr1.save()

    sr2 = SystemRelease()
    sr2.tag = "rhel-1.0"
    sr2.description = "Red Hat Enterprise Linux 1 release 0"
    sr2.active = True
    sr2.save()
    
    sr3 = SystemRelease()
    sr3.tag = "rhel-0.0"
    sr3.description = "Red Hat Enterprise Linux 0 release 0"
    sr3.active = False
    sr3.save()
    
    m1 = MockConfig()
    m1.name = "rhel-0.1"
    m1.enabled = True
    m1.save()
    
    t1 = Tag()
    t1.name = "rhel-0.1-pending"
    t1.release = sr1
    t1.mock = m1
    t1.save()

    m2 = MockConfig()
    m2.name = "rhel-1.0"
    m2.enabled = True
    m2.save()

    m3 = MockConfig()
    m3.name = "rhel-1.0-override"
    m3.enabled = False
    m3.save()
    
    t2 = Tag()
    t2.name = "rhel-1.0-pending"
    t2.release = sr2
    t2.mock = m2
    t2.save()
    
    t3 = Tag()
    t3.name = "rhel-1.0-release"
    t3.release = sr2
    t3.mock = m3
    t3.save()
    
    u = User()
    u.username = 'test_user'
    u.is_staff = False
    u.is_active = True
    u.is_superuser = False
    u.save()
    u.user_permissions.add(Permission.objects.get(codename='errata_xmlrpc_scan'))
    u.save()

    bad_user = User()
    bad_user.username = 'bad_user'
    bad_user.is_staff = False
    bad_user.is_active = True
    bad_user.is_superuser = False
    bad_user.save()

    c = Channel()
    c.name = "default"
    c.save()

    a = Arch()
    a.name = 'noarch'
    a.pretty_name = 'noarch'
    a.save()


def fill_db_waiving():
    """
    Fill database with data related to waiving
    """


def clear_all(model):
    if isinstance(model, list) or isinstance(model, tuple):
        for model_instance in model:
            for m in model_instance.objects.all():
                m.delete()        
    else:
        for m in model.objects.all():
            m.delete()


def clear_db():
    clear_all([Tag, MockConfig, SystemRelease, Channel, Arch, Package, User])