from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from authentication.models import Organization
from utils.permissions import IsOrganizationMember
from .models import Meter
from .serializers import MeterSerializer
from .token_serializers import GenerateTokenSerializer
from .utils import generate_meter_token


class MeterListCreateView(generics.ListCreateAPIView):
    serializer_class = MeterSerializer
    permission_classes = [IsAuthenticated, IsOrganizationMember]

    def get_queryset(self):
        return Meter.objects.filter(organization__uuid=self.kwargs['org_uuid'])

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        context['organization'] = Organization.objects.get(uuid=self.kwargs['org_uuid'])
        return context


class MeterDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = MeterSerializer
    permission_classes = [IsAuthenticated, IsOrganizationMember]
    lookup_field = 'uuid'
    lookup_url_kwarg = 'meter_uuid'

    def get_queryset(self):
        return Meter.objects.filter(organization__uuid=self.kwargs['org_uuid'])


class GenerateMeterTokenView(APIView):
    permission_classes = [IsAuthenticated, IsOrganizationMember]

    def post(self, request, *args, **kwargs):
        serializer = GenerateTokenSerializer(data=request.data)
        if serializer.is_valid():
            validated_data = serializer.validated_data

            # The meter number is in the request body, so we don't need to get it from the URL
            # meter = Meter.objects.get(uuid=self.kwargs['meter_uuid'])
            # validated_data['meter_number'] = meter.meter_number

            try:
                token_type = validated_data.get('token_type')
                response_data = generate_meter_token(token_type, validated_data)

                # Process the response based on token type
                if token_type == 'kct':
                    processed_response = [
                        {"description": item.get("description"), "token": item.get("tokenDec")}
                        for item in response_data.get('data', {}).get('data', [])
                    ]
                elif token_type in ['credit', 'clear_credit']:
                    # Ensure data is not empty before accessing index 0
                    data_list = response_data.get('data', {}).get('data', [])
                    if data_list:
                        processed_response = {"token": data_list[0].get("tokenDec")}
                    else:
                        processed_response = {"token": None}
                else:
                    processed_response = response_data

                return Response(processed_response, status=status.HTTP_200_OK)

            except Exception as e:
                return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
