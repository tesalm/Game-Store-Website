from django.conf.urls import url
from django.urls import path, include
from . import views


urlpatterns = [
    url(r"^$", views.index, name="index"),
    path('accounts/', include('django.contrib.auth.urls')),
    path("register/", views.register, name="register"),
    path("activate/<slug:uidb64>/<slug:token>/", views.activate, name='activate'),
    path("game_upload", views.GameUploadView.as_view(), name="game_upload"),
    path("game/<int:gid>/play", views.play, name="play"),
    path("game/<int:gid>/view", views.gameview, name="gameview"),
    path("game/<int:gid>/delete", views.deletegame, name="deletegame"),
    path("game/<int:gid>/edit", views.editgame, name="editgame"),
    path("game/<int:gid>/purchase", views.purchase, name="purchase"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("searchresult/", views.search, name="search"),
    path("payment_result/", views.payment_result, name="payment_result"),
    path("api/v1/sales.json", views.api_v1_sales, name="api-v1-sales"),
    path("api/v1/scores.json", views.api_v1_scores, name="api-v1-scores"),
    path("api/v1/games.json", views.api_v1_games, name="api-v1-games"),
    path("api/v1/", views.api_v1, name="api-v1"),
]
