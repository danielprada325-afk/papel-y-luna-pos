from django.urls import path
from api import routes

urlpatterns = [path("api/", routes.dispatch), path("api/<str:resource>/", routes.dispatch), path("api/<str:resource>/<path:record_id>", routes.dispatch)]
