from django.urls import path
from . import views
from . import api

urlpatterns = [
    path("api/", api.Dlist, name="json"),
    path("api/post/",api.Dhtviews.as_view(),name='json'),
    path("", views.dashboard, name="dashboard"),
    path("latest/", views.latest_json, name="latest_json"),
    path("graph_temp/", views.graph_temp, name="graph_temp"),
    path("graph_hum/", views.graph_hum, name="graph_hum"),
    path("incident/status/", api.IncidentStatus.as_view(), name="incident_status"),
    path("incident/update/", api.IncidentUpdateOperator.as_view(), name="incident_update"),
    path("incident/archive/", views.incident_archive, name="incident_archive"),
    path("incident/<int:pk>/", views.incident_detail, name="incident_detail"),
    ]
