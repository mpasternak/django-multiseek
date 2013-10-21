from django.core.urlresolvers import reverse
from django.shortcuts import redirect


def root(request):
    return redirect(reverse('multiseek:index'))