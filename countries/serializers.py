
from rest_framework import serializers
from countries.models import Country


class CountrySerializer(serializers.ModelSerializer):
    class Meta:
        model = Country
        fields = ['uuid', 'name', 'currency', 'currency_symbol']