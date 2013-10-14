# -*- encoding: utf-8 -*-


def make_field(klass, operation, value):
    return {
        u'field': unicode(klass.label),
        u'operation': unicode(operation),
        u'value': value}