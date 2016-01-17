from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^metainfos$', views.metainfos, name='metainfos'),
]
