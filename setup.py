"""Minimal setup.py — only custom build commands for locale compilation.

All package metadata lives in pyproject.toml. This file exists solely to
ensure ``django-admin compilemessages`` runs during wheel/sdist builds.
"""

import os

from setuptools import Command, setup
from setuptools.command.build_py import build_py as _build_py


class compile_translations(Command):
    description = "compile message catalogs to MO files via django compilemessages"
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        curdir = os.getcwd()
        os.chdir(os.path.join(os.path.dirname(__file__), "multiseek"))
        from django.core.management import call_command

        call_command("compilemessages")
        os.chdir(curdir)


class build_py(_build_py):
    """Run compilemessages before collecting Python files."""

    def run(self):
        self.run_command("compile_translations")
        _build_py.run(self)


setup(
    cmdclass={
        "compile_translations": compile_translations,
        "build_py": build_py,
    },
)
