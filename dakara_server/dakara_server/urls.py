"""Dakara server URL Configuration.

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
from django.conf import settings
from django.conf.urls import re_path
from django.contrib import admin
from django.contrib.staticfiles.views import serve
from django.urls import include, path
from rest_framework.documentation import include_docs_urls

from internal import views as internal_views
from library import views as library_views
from playlist import views as playlist_views
from users import views as users_views

urlpatterns = [
    # Admin route
    path("admin/", admin.site.urls),
    # Authentication routes
    path("api/accounts/", include("rest_registration.api.urls")),
    path("api/auth/", include("rest_framework.urls", namespace="rest_framework")),
    # API routes for internal
    path("api/settings/", internal_views.SettingsView.as_view(), name="settings"),
    # API routes for the users
    path("api/users/", users_views.UserListView.as_view(), name="users-list"),
    path("api/users/<int:pk>/", users_views.UserView.as_view(), name="users"),
    path(
        "api/users/current/",
        users_views.CurrentUserView.as_view(),
        name="users-current",
    ),
    # API routes for the playlist
    path(
        "api/playlist/player/status/",
        playlist_views.PlayerStatusView.as_view(),
        name="playlist-player-status",
    ),
    path(
        "api/playlist/player/errors/",
        playlist_views.PlayerErrorView.as_view(),
        name="playlist-player-errors",
    ),
    path(
        "api/playlist/player/command/",
        playlist_views.PlayerCommandView.as_view(),
        name="playlist-player-command",
    ),
    path(
        "api/playlist/player-token/",
        playlist_views.PlayerTokenListView.as_view(),
        name="playlist-player-token-list",
    ),
    path(
        "api/playlist/player-token/<int:pk>/",
        playlist_views.PlayerTokenView.as_view(),
        name="playlist-player-token",
    ),
    path(
        "api/playlist/digest/",
        playlist_views.DigestView.as_view(),
        name="playlist-digest",
    ),
    path(
        "api/playlist/entries/",
        playlist_views.PlaylistEntryListView.as_view(),
        name="playlist-entries-list",
    ),
    path(
        "api/playlist/entries/<int:pk>/",
        playlist_views.PlaylistEntryView.as_view(),
        name="playlist-entries",
    ),
    path(
        "api/playlist/played-entries/",
        playlist_views.PlaylistPlayedEntryListView.as_view(),
        name="playlist-played-entries-list",
    ),
    path(
        "api/playlist/karaoke/",
        playlist_views.KaraokeView.as_view(),
        name="playlist-karaoke",
    ),
    # API routes for the library
    path(
        "api/library/songs/",
        library_views.SongListView.as_view(),
        name="library-song-list",
    ),
    path(
        "api/library/songs/<int:pk>/",
        library_views.SongView.as_view(),
        name="library-song",
    ),
    path(
        "api/library/songs/retrieve/",
        library_views.SongRetrieveListView.as_view(),
        name="library-song-retrieve-list",
    ),
    path(
        "api/library/artists/",
        library_views.ArtistListView.as_view(),
        name="library-artist-list",
    ),
    path(
        "api/library/artists/prune/",
        library_views.ArtistPruneView.as_view(),
        name="library-artist-prune",
    ),
    path(
        "api/library/works/",
        library_views.WorkListView.as_view(),
        name="library-work-list",
    ),
    path(
        "api/library/works/<int:pk>/",
        library_views.WorkView.as_view(),
        name="library-work",
    ),
    path(
        "api/library/works/retrieve/",
        library_views.WorkRetrieveListView.as_view(),
        name="library-work-retrieve-list",
    ),
    path(
        "api/library/works/prune/",
        library_views.WorkPruneView.as_view(),
        name="library-work-prune",
    ),
    path(
        "api/library/work-types/",
        library_views.WorkTypeListView.as_view(),
        name="library-worktype-list",
    ),
    path(
        "api/library/work-types/<int:pk>/",
        library_views.WorkTypeView.as_view(),
        name="library-worktype",
    ),
    path(
        "api/library/song-tags/",
        library_views.SongTagListView.as_view(),
        name="library-songtag-list",
    ),
    path(
        "api/library/song-tags/<int:pk>/",
        library_views.SongTagView.as_view(),
        name="library-songtag",
    ),
    # API documentation routes
    path("api-docs/", include_docs_urls(title="Dakara server API")),
]

if settings.DEBUG:
    urlpatterns.extend(
        [
            # Default to main page
            re_path(
                r"^(?!api/|api-docs/?)",  # serve everything but the API routes
                # API documentation routes
                serve,
                kwargs={"path": "index.html"},
            )
        ]
    )
