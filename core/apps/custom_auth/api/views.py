from rest_framework import status

from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet
from rest_framework.generics import get_object_or_404
from . import serializers
from .. import models
from ..service.user_service.change_structure import CreateStructureUser


class CustomUserViewSet(ModelViewSet):
    """
    Представление для работы с CustomUser
    """
    queryset = models.CustomUser.objects.undeleted()
    serializer_class = serializers.CustomUserSerializer


class UserDetailView(ModelViewSet):
    queryset = models.CustomUser.objects \
        .prefetch_related('soldiers__service_records', 'role_users__role').undeleted()
    serializer_class = serializers.DetailUserSerializer


class UserBuilderApiView(APIView):
    """
    Прдеставления для работы с user,user_role,soldier,record
    """

    def get(self, request, *args, **kwargs):
        return Response(status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        data = CreateStructureUser(request.data).process()
        return Response(data, status=status.HTTP_201_CREATED)

    def patch(self, request, *args, **kwargs):
        data = CreateStructureUser(request.data, CreateStructureUser.PROCESS_TYPE_UPDATE).process()
        return Response(data, status=status.HTTP_200_OK)

    def delete(self, request, *args, **kwargs):
        data = CreateStructureUser(request.data, CreateStructureUser.PROCESS_TYPE_DELETE).process()
        return Response(data, status=status.HTTP_204_NO_CONTENT)
