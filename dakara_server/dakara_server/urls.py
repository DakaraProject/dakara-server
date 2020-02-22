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
from django.conf.urls import url
from django.contrib import admin
from django.conf import settings
from django.contrib.staticfiles.views import serve
from django.urls import include
from rest_framework.authtoken.views import obtain_auth_token
from rest_framework.documentation import include_docs_urls

from library import views as library_views
from playlist import views as playlist_views
from users import views as users_views
from internal import views as internal_views


urlpatterns = [
    # Admin route
    url(r"^admin/", admin.site.urls),
    # Authentication routes
    url(r"^api/auth/", include("rest_framework.urls", namespace="rest_framework")),
    url(r"^api/token-auth/", obtain_auth_token),
    # API routes for internal
    url(r"^api/version/$", internal_views.VersionView.as_view(), name="version"),
    # API routes for the users
    url(r"^api/users/$", users_views.UserListView.as_view(), name="users-list"),
    url(
        r"^api/users/(?P<pk>[0-9]+)/$",
        users_views.UserView.as_view(),
        name="users-detail",
    ),
    url(
        r"^api/users/(?P<pk>[0-9]+)/password/$",
        users_views.PasswordView.as_view(),
        name="users-password",
    ),
    url(
        r"^api/users/current/$",
        users_views.CurrentUserView.as_view(),
        name="users-current",
    ),
    # API routes for the playlist
    url(
        r"^api/playlist/player/status/$",
        playlist_views.PlayerStatusView.as_view(),
        name="playlist-player-status",
    ),
    url(
        r"^api/playlist/player/errors/$",
        playlist_views.PlayerErrorView.as_view(),
        name="playlist-player-errors",
    ),
    url(
        r"^api/playlist/player/command/$",
        playlist_views.PlayerCommandView.as_view(),
        name="playlist-player-command",
    ),
    url(
        r"^api/playlist/digest/$",
        playlist_views.DigestView.as_view(),
        name="playlist-digest",
    ),
    url(
        r"^api/playlist/entries/$",
        playlist_views.PlaylistEntryListView.as_view(),
        name="playlist-entries-list",
    ),
    url(
        r"^api/playlist/entries/(?P<pk>[0-9]+)/$",
        playlist_views.PlaylistEntryView.as_view(),
        name="playlist-entries-detail",
    ),
    url(
        r"^api/playlist/played-entries/$",
        playlist_views.PlaylistPlayedEntryListView.as_view(),
        name="playlist-played-entries-list",
    ),
    url(
        r"^api/playlist/karaoke/$",
        playlist_views.KaraokeView.as_view(),
        name="playlist-karaoke",
    ),
    # API routes for the library
    url(
        r"^api/library/songs/$",
        library_views.SongListView.as_view(),
        name="library-song-list",
    ),
    url(
        r"^api/library/artists/$",
        library_views.ArtistListView.as_view(),
        name="library-artist-list",
    ),
    url(
        r"^api/library/works/$",
        library_views.WorkListView.as_view(),
        name="library-work-list",
    ),
    url(
        r"^api/library/work-types/$",
        library_views.WorkTypeListView.as_view(),
        name="library-worktype-list",
    ),
    url(
        r"^api/library/song-tags/$",
        library_views.SongTagListView.as_view(),
        name="library-songtag-list",
    ),
    url(
        r"^api/library/songs/(?P<pk>[0-9]+)/$",
        library_views.SongView.as_view(),
        name="library-song-detail",
    ),
    url(
        r"^api/library/song-tags/(?P<pk>[0-9]+)/$",
        library_views.SongTagView.as_view(),
        name="library-songtag-detail",
    ),
    # API route for the feeder
    url(
        r"^api/library/feeder/retrieve/$",
        library_views.feeder.FeederListView.as_view(),
        name="library-feeder-list",
    ),
    # API documentation routes
    url(r"^api-docs/", include_docs_urls(title="Dakara server API")),
]

if settings.DEBUG:
    urlpatterns.extend(
        [
            # Default to main page
            url(
                r"^(?!api/|api-docs/?)",  # serve everything but the API routes
                # API documentation routes
                serve,
                kwargs={"path": "index.html"},
            )
        ]
    )
