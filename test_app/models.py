from django.db import models

class Language(models.Model):
    name = models.TextField()
    description = models.TextField()

    def __unicode__(self):
        return self.name


class Author(models.Model):
    last_name = models.TextField()
    first_name = models.TextField()

    def __unicode__(self):
        return u"%s %s" % (self.first_name, self.last_name)


class Book(models.Model):
    title = models.TextField()
    year = models.IntegerField()
    language = models.ForeignKey(Language)
    authors = models.ManyToManyField(Author)
    no_editors = models.IntegerField()
    last_updated = models.DateField(auto_now=True)

    def __unicode__(self):
        return u"%s by %s" % (self.title, u", ".join(
            [unicode(author) for author in self.authors.all()]))