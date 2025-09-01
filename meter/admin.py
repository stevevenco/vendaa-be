from django.contrib import admin

# Register your models here.
from config.admin import admin_site
from meter.models import Meter

admin_site.register(Meter)
