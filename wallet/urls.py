from django.urls import path
from .views import CreateWalletView, WalletBalanceView, InitiatePaymentView, TransactionListView

urlpatterns = [
    path('wallet/create/<uuid:organization_id>/', CreateWalletView.as_view(), name='create-wallet'),
    path('wallet/balance/<uuid:organization_id>/', WalletBalanceView.as_view(), name='wallet-balance'),
    path('wallet/initiate-payment/<uuid:organization_id>', InitiatePaymentView.as_view(), name='initiate-payment'),
    path('wallet/transactions/<uuid:organization_id>/', TransactionListView.as_view(), name='transaction-list'),
]
