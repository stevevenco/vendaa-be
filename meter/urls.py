from django.urls import path


urlpatterns = [
    path('meters/', MeterListView.as_view(), name='meter-list'),
    path('meters/<int:pk>/', MeterDetailView.as_view(), name='meter-detail'),
    path('meters/add/', MeterCreateView.as_view(), name='meter-add'),
    path('meters/<int:pk>/edit/', MeterUpdateView.as_view(), name='meter-edit'),
    path('meters/<int:pk>/delete/', MeterDeleteView.as_view(), name='meter-delete'),
]