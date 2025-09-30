from django.urls import include, path
from countries.views import ListCountries

urlpatterns = [
    path("countries/", ListCountries.as_view(), name="countries-list"),
]