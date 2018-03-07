# -*- encoding: utf-8 -*-

import os
import sys

from setuptools import setup, Command
from distutils.command.build import build as _build
from setuptools.command.install_lib import install_lib as _install_lib
from distutils.cmd import Command


class compile_translations(Command):
    description = 'compile message catalogs to MO files via django compilemessages'
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        curdir = os.getcwd()
        os.chdir(os.path.realpath('multiseek'))
        from django.core.management import call_command
        call_command('compilemessages')
        os.chdir(curdir)


class build(_build):
    sub_commands = [('compile_translations', None)] + _build.sub_commands


class install_lib(_install_lib):
    def run(self):
        self.run_command('compile_translations')
        _install_lib.run(self)



# Utility function to read the README file.
# Used for the long_description. It's nice, because now 1) we have a top level
# README file and 2) it's easier to type in the README file than to put a raw
# string in below ...
def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


class RunTests(Command):
    description = "Run the django test suite from the testproj dir."

    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        this_dir = os.getcwd()
        testproj_dir = os.path.join(this_dir, "test_project")
        os.chdir(testproj_dir)
        sys.path.append(testproj_dir)
        from django.core.management import execute_manager

        os.environ["DJANGO_SETTINGS_MODULE"] = 'test_project.settings'
        settings_file = os.environ["DJANGO_SETTINGS_MODULE"]
        settings_mod = __import__(settings_file, {}, {}, [''])
        execute_manager(settings_mod, argv=[
            __file__, "test", "multiseek", "--traceback"])
        os.chdir(this_dir)


if 'sdist' in sys.argv:
    # clear compiled mo files before building the distribution
    walk = os.walk(os.path.join(os.getcwd(), 'multiseek/locale'))
    for dirpath, dirnames, filenames in walk:
        if not filenames:
            continue

        for fn in ['django.mo', 'djangojs.mo']:
            if fn in filenames:
                os.unlink(os.path.join(dirpath, fn))

else:
    # Always try to build messages, fail if django not present
    # (I hate incomplete releases)
    dir = os.getcwd()
    os.chdir(os.path.join(dir, 'multiseek'))
    os.system('django-admin.py compilemessages')
    os.chdir(dir)

def reqs(f):
    for elem in open(f).readlines():
        elem = elem.strip()

        if not elem:
            continue
        
        if elem.find("#egg=")>0:
            ign, egg = elem.split("#egg=")
            yield egg
            continue
        
        if elem.startswith("#") or elem.startswith("-r"):
            continue
        
        yield elem

        
setup(
    name='django-multiseek',
    version='0.9.34',
    description='Build a form to seek records using multiple parameters',
    author=u'Michał Pasternak',
    author_email='michal.dtz@gmail.com',
    url='http://TODO',
    packages=['multiseek'],
    package_data={'multiseek': [
        'locale/*/LC_MESSAGES/*',
        'static/multiseek/*.js',
        'static/multiseek/*.css',
        'templates/multiseek/*.html']},
    include_package_data=True,
    zip_safe=False,
    long_description=read("README.md"),
    license='MIT',
    keywords='django multiseek',
    install_requires=["Django>=1.11"] + list(reqs("requirements.txt")),
    tests_require=["Django>=1.11"] + list(reqs("requirements_dev.txt")),
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
    cmdclass={'build': build, 'install_lib': install_lib,
              'compile_translations': compile_translations,
              'test': RunTests},
)
