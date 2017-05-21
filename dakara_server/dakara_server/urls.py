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
from django.conf import settings
from django.views.defaults import page_not_found
from rest_framework.authtoken.views import obtain_auth_token
from library.views import *
from playlist.views import *

urlpatterns = [

    # Admin route
    url(r'^admin/', include(admin.site.urls)),

    # Authentication routes
    url(r'^api/auth/', include('rest_framework.urls', namespace='rest_framework')),
    url(r'^api/token-auth/', obtain_auth_token),

    # Api routes for the player
    url(r'^api/player/status/$', PlayerForPlayerView.as_view()),
    url(r'^api/player/error/$', PlayerErrorForPlayerView.as_view()),

    # Api routes for the front
    url(r'^api/playlist/player/manage/$', PlayerCommandForUserView.as_view()),
    url(r'^api/playlist/player/status/$', PlayerForUserView.as_view()),
    url(r'^api/playlist/player/errors/$', PlayerErrorsForUserView.as_view()),
    url(r'^api/playlist/player/$', PlayerDetailsCommandErrorsForUserView.as_view()),
    url(r'^api/playlist/$', PlaylistEntryList.as_view()),
    url(r'^api/playlist/(?P<pk>[0-9]+)/$', PlaylistEntryDetail.as_view()),
    url(r'^api/library/songs/$', SongList.as_view()),
    url(r'^api/library/artists/$', ArtistList.as_view()),
    url(r'^api/library/works/$', WorkList.as_view()),
    url(r'^api/library/work-types/$', WorkTypeList.as_view()),
    url(r'^api/library/songs/(?P<pk>[0-9]+)/$', SongDetailView.as_view(), name='song-detail'),

    # Default case for api routes
    url(r'^api', page_not_found),

]

if settings.DEBUG:
    urlpatterns.extend([
            # Default to main page
            url(r'', 'django.contrib.staticfiles.views.serve', kwargs={
                            'path': 'index.html'})
        ])
