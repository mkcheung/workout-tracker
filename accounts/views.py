from accounts.serializers import (
    RegisterSerializer,
    LoginSerializer
)
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework.authtoken.models import Token

from .serializers import MeSerializer

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def register(request):
    serializer = RegisterSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    user = serializer.save()

    token, _ = Token.objects.get_or_created(user=user)
    return Response({
        'token':token.key,
        "user": {
            "id": user.id,
            "name": user.name, 
            "email": user.email
        },
    }, status=status.HTTP_201_CREATED)

@api_view(['POST'])
@permission_classes([AllowAny])
def login(request):
    serializer = LoginSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    user = serializer.validated_data['user']
    token, _ = Token.objects.get_or_created(user=user)
    return Response({'token': token.key}, status=status.HTTP_200_OK)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout(request):
    request.auth.delete()
    return Response({'message':'Logged Out'}, status=status.HTTP_200_OK)

@api_view(['GET', 'PATCH'])
@permission_classes([IsAuthenticated])
def me(request):
    if request.method == 'GET':
        return Response(MeSerializer(request.user).data)

        serializer = MeSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)