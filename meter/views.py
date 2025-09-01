from rest_framework import generics, status, serializers
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

import meter

from .models import Meter
from .serializers import MeterSerializer
from rest_framework.views import APIView
from .utils import add_meter_to_service


# class MeterListCreateView(generics.ListCreateAPIView):
#     queryset = Meter.objects.all()
#     serializer_class = MeterSerializer
#     permission_classes = [IsAuthenticated]

#     def post(self, request):
#         serializer = MeterSerializer(data=request.data, added_by=self.request.user)
#         if not serializer.is_valid():
            
#         try:
#             response_from_service = add_meter_to_service(meter.meter_number)
#             if response_from_service is None or response_from_service.get('response', {}).get('status') != 'success':
#                 meter.delete()
#                 raise serializers.ValidationError({"detail": "Failed to add meter to external service."})
#         except Exception as e:
#             meter.delete()
#             raise serializers.ValidationError({"detail": f"An error occurred while adding meter to external service: {e}"})

class MeterListCreateView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = MeterSerializer

    def get(self, request, *args, **kwargs):
        organization_id = request.query_params.get('org_uuid')
        meters = Meter.objects.filter(organization_id=organization_id)
        serializer = MeterSerializer(meters, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializers = MeterSerializer(data=request.data, context={'added_by': request.user})
        if serializers.is_valid():
            meter = serializers.save()
            response_serializer = MeterSerializer(meter)
            return Response({
                'message': 'Meter created successfully',
                'data': response_serializer.data
            }, status=status.HTTP_201_CREATED)
        return Response(serializers.errors, status=status.HTTP_400_BAD_REQUEST)

class MeterDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Meter.objects.all()
    serializer_class = MeterSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'uuid'
    lookup_url_kwarg = 'meter_uuid'
