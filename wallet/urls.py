from django.urls import path
from .views import CreateWalletView, WalletBalanceView, InitiatePaymentView

urlpatterns = [
    path('create/', CreateWalletView.as_view(), name='create-wallet'),
    path('balance/<uuid:organization_id>/', WalletBalanceView.as_view(), name='wallet-balance'),
    path('initiate-payment/<uuid:organization_id>', InitiatePaymentView.as_view(), name='initiate-payment'),  # Removed trailing slash
]
