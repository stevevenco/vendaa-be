from django.urls import path
from . import views

urlpatterns = [
    # API Key management endpoints
    path('organizations/<uuid:org_uuid>/api-keys/', 
        views.APIKeyListView.as_view(), name='apikey-list'),
    path('organizations/<uuid:org_uuid>/api-keys/create/', 
        views.APIKeyCreateView.as_view(), name='apikey-create'),
    path('organizations/<uuid:org_uuid>/api-keys/<uuid:key_uuid>/', 
        views.APIKeyDetailView.as_view(), name='apikey-detail'),
    path('organizations/<uuid:org_uuid>/api-keys/<uuid:key_uuid>/regenerate/', 
        views.regenerate_api_key, name='apikey-regenerate'),
    
    # Auth context endpoint
    path('key-auth/me/', views.api_auth_me, name='key-auth-me'),
]