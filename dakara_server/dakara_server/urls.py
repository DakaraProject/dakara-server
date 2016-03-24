"""dakara_server URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.8/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Add an import:  from blog import urls as blog_urls
    2. Add a URL to urlpatterns:  url(r'^blog/', include(blog_urls))
"""
from django.conf.urls import include, url
from django.contrib import admin
from django.views.generic import TemplateView
from library.views import *
from playlist.views import *

urlpatterns = [
    # Root
    url(r'^$', TemplateView.as_view(template_name='index.html')),

    url(r'^admin/', include(admin.site.urls)),
    url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    #route for the player
    url(r'^player/status/$', PlayerForPlayerView.as_view()),
    url(r'^player/error/$', PlayerErrorForPlayerView.as_view()),

    #routes for the user
    url(r'^playlist/player/manage/$', PlayerCommandForUserView.as_view()),
    url(r'^playlist/player/status/$', PlayerForUserView.as_view()),
    url(r'^playlist/player/errors/$', PlayerErrorsForUserView.as_view()),
    url(r'^playlist/$', PlaylistEntryList.as_view()),
    url(r'^playlist/(?P<pk>[0-9]+)/$', PlaylistEntryDetail.as_view()),
    url(r'^library/songs/$', SongList.as_view()),
    url(r'^library/songs/(?P<pk>[0-9]+)/$', SongDetailView.as_view(), name='song-detail'),
]

