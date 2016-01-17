from django.http import HttpResponse
from nomadtoolkit.metaviewer.backend.contents import get_metainfos


def metainfos(request):
    metainfos = get_metainfos()
    return HttpResponse(metainfos)
