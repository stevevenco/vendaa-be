
# Register your models here.
from config.admin import admin_site
from wallet.models import Wallet, Transaction

admin_site.register(Wallet)
admin_site.register(Transaction)
