# -*- coding: utf-8 -*-
from .controllers import *

urls = (
    (r'^/?$', index),
    (r'^/admin/?$', admin),
    (r'^/admin/create$', admin_create),
    (r'^/admin/update$', admin_update),
    (r'^/admin/delete$', admin_delete),
    (r'^/admin/classes_admin', admin_classes),
    (r'^/admin/object_create', create_object),
    (r'^/admin/object_delete', delete_object),
    (r'^/admin/class_admin$', admin_class),
    (r'^/admin/class_delete$', delete_in_class),
    (r'^/admin/search$', search_object),
    (r'/test/(?P<id>.*)$', test),
    (r'^/test/?$', test),
    (r'^/list_classes', list_classes),
    (r'^/list_classes?$', list_classes),
    (r'^/collections', collections),
    (r'^/collections?$', collections),
    (r'^/issue?$', issue),
    (r'^/issue', issue),
    (r'^/show_object?$', show_object),
    (r'^/show_object_detailled?$', show_object_detailled),
    (r'^/show_class?$', show_class),
    (r'^/signin', signin),
    (r'^/signout', signout)
)
