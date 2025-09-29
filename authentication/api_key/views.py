
from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication

from django.shortcuts import get_object_or_404
from django.db import transaction as db_transaction

from authentication.api_key.authentication import APIKeyAuthentication
from utils.permissions import HasOrgPermission
from .models import APIKey
from authentication.models import Organization
from .permissions import IsOrganizationOwnerOrAdminOrAPIKey, AuthReadPermission
from .serializers import (
    APIKeySerializer, CreateAPIKeySerializer, APIKeyResponseSerializer
)
from .services import get_api_key_service, ApiKeyService, ProductionApiKeyService, SandboxApiKeyService


class APIKeyListView(generics.ListAPIView):
    """List API keys for an organization"""
    authentication_classes = [
        APIKeyAuthentication,
        JWTAuthentication
    ]
    serializer_class = APIKeySerializer
    permission_classes = [
        IsAuthenticated,
        HasOrgPermission('developer', 'read'),
        # IsOrganizationOwnerOrAdminOrAPIKey
    ]
    
    def get_queryset(self):
        org_uuid = self.kwargs['org_uuid']
        organization=get_object_or_404(Organization, uuid=org_uuid)
        print(f"Fetching API keys for organization UUID: {org_uuid}")
        api_key_service = get_api_key_service(organization, self.request.user)
        api_keys = api_key_service.get_api_keys(organization)
        # api_keys = APIKey.objects.filter(organization__uuid=org_uuid)
        print(f"\n\nFound {api_keys.count()} API keys")
        return api_keys
        # return APIKey.objects.filter(organization__uuid=org_uuid)


class APIKeyCreateView(generics.CreateAPIView):
    """Create a new API key for an organization"""
    
    serializer_class = CreateAPIKeySerializer
    permission_classes = [IsAuthenticated, IsOrganizationOwnerOrAdminOrAPIKey]
    
    def create(self, request, *args, **kwargs):
        org_uuid = self.kwargs['org_uuid']
        organization = get_object_or_404(Organization, uuid=org_uuid)
        
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Create the API key
        try:
            # Determine created_by based on authentication type
            created_by = None
            if not hasattr(request.user, 'is_api_key_user'):
                created_by = request.user
                
            api_key, full_key = APIKey.create_api_key(
                organization=organization,
                key_type=serializer.validated_data['key_type'],
                name=serializer.validated_data.get('name'),
                created_by=created_by,
                is_sandbox=organization.is_sandbox
            )
            
            # Return the API key with the full key (only shown once)
            response_serializer = APIKeyResponseSerializer(api_key)
            response_data = response_serializer.data
            response_data['full_key'] = full_key
            
            return Response(response_data, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        org_uuid = self.kwargs['org_uuid']
        context['organization'] = get_object_or_404(Organization, uuid=org_uuid)
        return context


class APIKeyDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update, or delete an API key"""
    
    serializer_class = APIKeySerializer
    permission_classes = [IsAuthenticated, IsOrganizationOwnerOrAdminOrAPIKey]
    lookup_field = 'uuid'
    lookup_url_kwarg = 'key_uuid'
    
    def get_queryset(self):
        organization = get_object_or_404(Organization, uuid=self.kwargs['org_uuid'])
        api_key_service = get_api_key_service(organization, self.request.user)
        return api_key_service.get_api_keys(organization)
        # return APIKey.objects.filter(organization__uuid=self.kwargs['org_uuid'])
    
    def update(self, request, *args, **kwargs):
        # Only allow updating name and is_active fields
        allowed_fields = {'name', 'is_active'}
        for field in request.data:
            if field not in allowed_fields:
                return Response(
                    {'error': f'Field "{field}" cannot be updated'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        return super().update(request, *args, **kwargs)


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsOrganizationOwnerOrAdminOrAPIKey])
def regenerate_api_key(request, org_uuid, key_uuid):
    """Regenerate an existing API key"""
    
    organization = get_object_or_404(Organization, uuid=org_uuid)
    api_key_service = get_api_key_service(organization, request.user)
    api_key = api_key_service.get_api_key_by_uuid(key_uuid, organization)
    print(f"\n\nRegenerating API key {key_uuid} for organization {org_uuid}\n\n")
    # api_key = get_object_or_404(APIKey, uuid=key_uuid, organization=organization)

    with db_transaction.atomic():
        try:
            # Delete old key
            key_type = api_key.key_type
            is_sandbox = api_key.is_sandbox
            name = api_key.name
            api_key.delete()
            
            # Create new key
            created_by = None
            if not hasattr(request.user, 'is_api_key_user'):
                created_by = request.user
                
            new_api_key, full_key = APIKey.create_api_key(
                organization=organization,
                key_type=key_type,
                name=name,
                created_by=created_by,
                is_sandbox=is_sandbox
            )
            
            # Return the new API key with full key
            response_serializer = APIKeyResponseSerializer(new_api_key)
            response_data = response_serializer.data
            response_data['full_key'] = full_key
            
            return Response(response_data, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )


@api_view(['GET'])
@permission_classes([IsAuthenticated, AuthReadPermission])
def api_auth_me(request):
    """Get current authentication context (for API key validation)"""
    
    if hasattr(request.user, 'is_api_key_user'):
        # API key authentication
        api_key = request.auth
        return Response({
            'auth_type': 'api_key',
            'key_uuid': api_key.uuid,
            'key_type': api_key.key_type,
            'organization': {
                'uuid': api_key.organization.uuid,
                'uuid': str(api_key.organization.uuid),
                'name': api_key.organization.name,
            },
            'scopes': api_key.get_scopes(),
            'last_used_at': api_key.last_used_at,
        })
    else:
        # JWT authentication
        return Response({
            'auth_type': 'jwt',
            'user': {
                'uuid': request.user.uuid,
                'email': request.user.email,
            }
        })
