from django.shortcuts import render
from decimal import Decimal
import json
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404

from meter.serializers import MeterSerializer
from meter.models import Meter

# Create your views here.
# token_type

class MeterListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        meters = Meter.objects.all()
        serializer = MeterSerializer(meters, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
