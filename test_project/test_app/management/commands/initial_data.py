# -*- encoding: utf-8 -*-

from django.core.management.base import BaseCommand, CommandError

class Command(BaseCommand):
    help = 'Installs initial_data'

    def handle(self, *args, **options):
        from test_app.conftest import initial_data
        initial_data()