from __future__ import unicode_literals
from django.db import models
try:
    from builtins import str as text
except ImportError:
    text = unicode

from django.utils.encoding import python_2_unicode_compatible


@python_2_unicode_compatible
class Language(models.Model):
    name = models.TextField()
    description = models.TextField()

    def __str__(self):
        return self.name

@python_2_unicode_compatible
class Author(models.Model):
    last_name = models.TextField()
    first_name = models.TextField()

    def __str__(self):
        return u"%s %s" % (self.first_name, self.last_name)


@python_2_unicode_compatible
class Book(models.Model):
    title = models.TextField()
    year = models.IntegerField()
    language = models.ForeignKey(Language)
    authors = models.ManyToManyField(Author)
    no_editors = models.IntegerField()
    last_updated = models.DateField(auto_now=True)
    available = models.BooleanField(default=False)

    def __str__(self):
        return u"%s by %s" % (self.title, u", ".join(
            [text(author) for author in self.authors.all()]))