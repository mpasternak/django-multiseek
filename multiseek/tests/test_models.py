# -*- encoding: utf-8 -*-

from django.contrib.auth.models import AnonymousUser, User
from django.test import TransactionTestCase
from multiseek.models import SearchForm
from model_bakery import baker


class TestModels(TransactionTestCase):
    def test_search_form_manager(self):
        u = baker.make(User)

        s1 = baker.make(SearchForm, owner=u, public=False, name='A')
        s2 = baker.make(SearchForm, owner=u, public=True, name='B')

        res = SearchForm.objects.get_for_user(AnonymousUser())
        self.assertEqual(list(res), [s2])

        res = SearchForm.objects.get_for_user(u)
        self.assertEqual(list(res), [s1, s2])