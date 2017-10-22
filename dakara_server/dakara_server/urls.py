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
from users.views import *

import logging

logger = logging.getLogger("django")
logger.info("Dakara server {} ({})".format(settings.VERSION, settings.DATE))

urlpatterns = [

    # Admin route
    url(r'^admin/', include(admin.site.urls)),

    # Authentication routes
    url(r'^api/auth/', include('rest_framework.urls', namespace='rest_framework')),
    url(r'^api/token-auth/', obtain_auth_token),

    # Api routes for the users
    url(r'^api/users/$', UserList.as_view(), name='users-list'),
    url(r'^api/users/(?P<pk>[0-9]+)/$', UserView.as_view(), name='users-detail'),
    url(r'^api/users/(?P<pk>[0-9]+)/password/$', PasswordView.as_view(), name='users-password'),
    url(r'^api/users/current/$', CurrentUser.as_view(), name='users-current'),

    # Api routes for the player
    url(r'^api/player/status/$', PlayerForPlayerView.as_view(), name='player-status'),
    url(r'^api/player/error/$', PlayerErrorForPlayerView.as_view(), name='player-error'),

    # Api routes for the playlist
    url(r'^api/playlist/player/manage/$', PlayerCommandForUserView.as_view(), name='playlist-player-manage'),
    url(r'^api/playlist/player/status/$', PlayerForUserView.as_view(), name='playlist-player-status'),
    url(r'^api/playlist/player/errors/$', PlayerErrorsForUserView.as_view(), name='playlist-player-errors'),
    url(r'^api/playlist/player/$', PlayerDetailsCommandErrorsForUserView.as_view(), name='playlist-player'),
    url(r'^api/playlist/$', PlaylistEntryList.as_view(), name='playlist-list'),
    url(r'^api/playlist/(?P<pk>[0-9]+)/$', PlaylistEntryDetail.as_view(), name='playlist-detail'),

    # Api routes for the library
    url(r'^api/library/songs/$', SongList.as_view(), name='library-song-list'),
    url(r'^api/library/artists/$', ArtistList.as_view(), name='library-artist-list'),
    url(r'^api/library/works/$', WorkList.as_view(), name='library-work-list'),
    url(r'^api/library/work-types/$', WorkTypeList.as_view(), name='library-worktype-list'),
    url(r'^api/library/songs/(?P<pk>[0-9]+)/$', SongDetailView.as_view(), name='library-song-detail'),

]

if settings.DEBUG:
    urlpatterns.extend([
            # Default case for api routes
            url(r'^api/', page_not_found),
            # Default to main page
            url(r'', 'django.contrib.staticfiles.views.serve', kwargs={
                            'path': 'index.html'})
        ])
