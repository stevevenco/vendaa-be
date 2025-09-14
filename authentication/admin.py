from authentication.models import (
  OTP, Membership, Organization, User,
  Invitation
  )
from authentication.api_key.models import APIKey
from config.admin import admin_site

admin_site.register(User)
admin_site.register(OTP)
admin_site.register(Organization)
admin_site.register(Membership)
admin_site.register(Invitation)
admin_site.register(APIKey)
