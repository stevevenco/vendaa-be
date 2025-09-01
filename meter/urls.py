from django.urls import path
from .views import MeterListCreateView, MeterDetailView, GenerateMeterTokenView

urlpatterns = [
    path('organizations/<uuid:org_uuid>/meters/', MeterListCreateView.as_view(), name='meter-list-create'),
    path('organizations/<uuid:org_uuid>/meters/<uuid:meter_uuid>/', MeterDetailView.as_view(), name='meter-detail'),
    path('organizations/<uuid:org_uuid>/generate-token/', GenerateMeterTokenView.as_view(), name='generate-meter-token'),
]