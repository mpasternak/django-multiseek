
from django.db import models
from django.db.models import Q
from django.utils.translation import ugettext_lazy as _
from django.conf import settings
from django.utils.encoding import python_2_unicode_compatible

class SearchFormManager(models.Manager):
    def get_for_user(self, user):
        if user.is_anonymous:
            return self.filter(public=True)

        return self.filter(
            Q(public=True) | Q(owner=user))


@python_2_unicode_compatible
class SearchForm(models.Model):
    name = models.TextField(verbose_name=_("Name"), unique=True)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL,
                              on_delete=models.CASCADE)
    public = models.BooleanField(
        verbose_name=_("Public"),
        default=False, help_text=_(
            "Make this search publicly available?"))
    data = models.TextField(verbose_name=_("Form data (JSON)"))

    objects = SearchFormManager()

    class Meta:
        ordering = ['name',]

    def __str__(self):
        return self.name
