from django.urls import path
from .views import MeterListCreateView, MeterDetailView, GenerateMeterTokenView, UtilityCostListCreateView, UtilityCostUpdateDeleteView, UtilityVendsListView

urlpatterns = [
    path('organizations/<uuid:org_uuid>/meters/', MeterListCreateView.as_view(), name='meter-list-create'),
    path('organizations/<uuid:org_uuid>/meters/<uuid:meter_uuid>/', MeterDetailView.as_view(), name='meter-detail'),
    path('organizations/<uuid:org_uuid>/generate-token/', GenerateMeterTokenView.as_view(), name='generate-meter-token'),
    path('meters/utility-costs/', UtilityCostListCreateView.as_view(), name='utility-cost-list-create'),
    path('meters/utility-costs/<uuid:uuid>/', UtilityCostUpdateDeleteView.as_view(), name='utility-cost-update-delete'),
    path('organizations/<uuid:org_uuid>/utility-vends/', UtilityVendsListView.as_view(), name='utility-vends-list')
]
