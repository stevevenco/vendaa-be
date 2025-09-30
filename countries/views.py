from django.shortcuts import render
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from countries.models import Country
from countries.serializers import CountrySerializer
# Create your views here.

class ListCountries(APIView):
    """
    View to list all countries in the system.

    * Requires no authentication.
    """

    permission_classes = [permissions.AllowAny]

    def get(self, request, format=None):
        """
        Return a list of all countries.
        """
        countries = Country.objects.all()
        serializer = CountrySerializer(countries, many=True)
        return Response(serializer.data)