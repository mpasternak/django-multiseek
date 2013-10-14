# -*- encoding: utf-8 -*-
from django.contrib.auth.models import AnonymousUser, User

from django.test import TransactionTestCase
from django_any import any_model
from multiseek.models import SearchForm



class TestModels(TransactionTestCase):
    def test_search_form_manager(self):
        u = any_model(User)

        s1 = any_model(SearchForm, owner=u, public=False, name='A')
        s2 = any_model(SearchForm, owner=u, public=True, name='B')

        res = SearchForm.objects.get_for_user(AnonymousUser())
        self.assertEquals(list(res), [s2])

        res = SearchForm.objects.get_for_user(u)
        self.assertEquals(list(res), [s1, s2])