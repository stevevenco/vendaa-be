from django.urls import path
from .views import MeterListCreateView, MeterDetailView

urlpatterns = [
    path('meters/organizations/<uuid:org_uuid>/', MeterListCreateView.as_view(), name='meter-list-create'),
    path('meters/<uuid:meter_uuid>/organizations/<uuid:org_uuid>/', MeterDetailView.as_view(), name='meter-detail'),
]