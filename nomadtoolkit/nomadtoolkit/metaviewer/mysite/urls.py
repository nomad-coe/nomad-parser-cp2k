from django.conf.urls import include, url
from django.contrib import admin

urlpatterns = [
    url(r'^', include('nomadtoolkit.metaviewer.frontend.urls')),
    url(r'^', include('nomadtoolkit.metaviewer.backend.urls')),
    url(r'^admin/', admin.site.urls),
]
