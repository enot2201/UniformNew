from rest_framework.views import APIView
from .service import DangerLevelService
from rest_framework.response import Response
from rest_framework import status


class GetDangerLevel(APIView):
    """
    Представление для получения уровня опасности данных
    """

    def get(self, request, *args, **kwargs):
        data = DangerLevelService(request.data).process()
        return Response(data, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        data = DangerLevelService(request.data).process()
        return Response(data, status=status.HTTP_201_CREATED)

    def patch(self, request, *args, **kwargs):
        data = DangerLevelService(request.data).process()
        return Response(data, status=status.HTTP_200_OK)
