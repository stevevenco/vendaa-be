from django.contrib import admin


class VendaaAdminSite(admin.AdminSite):
    site_header = "Vendaa Administration"
    site_title = "Vendaa"
    index_title = "Vendaa Administration"
    empty_value_display = "- - - -"


admin_site = VendaaAdminSite(name="Vendaa Admin Site")
