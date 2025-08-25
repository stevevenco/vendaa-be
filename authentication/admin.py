from authentication.models import OTP, Membership, Organization, User
from config.admin import admin_site

admin_site.register(User)
admin_site.register(OTP)
admin_site.register(Organization)
admin_site.register(Membership)
