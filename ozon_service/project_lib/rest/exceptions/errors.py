import logging

from rest_framework import exceptions
from rest_framework import status
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response

logger = logging.getLogger(__name__)

__ALL__ = (
    'ApiException', 'BadRequestError', 'ServiceUnavailable', 'ServerError', 'Conflict', 'ClientLimitError',
    'ExceptionResponse',
)


class ApiException(exceptions.APIException):
    """
    Ошибка API
    """

    def __init__(self, detail=None, status_code=None):
        if status_code is not None:
            self.status_code = status_code
        self.detail = detail


class BadRequestError(ApiException):
    status_code = status.HTTP_400_BAD_REQUEST

    def __init__(self, detail="Некорректный запрос."):
        super(BadRequestError, self).__init__(detail)


class ServiceUnavailable(exceptions.APIException):
    status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    def __init__(self, detail="Сервер администрирования недоступен."):
        super(ServiceUnavailable, self).__init__(detail)


class ServerError(exceptions.APIException):
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR

    def __init__(self, detail="Ошибка сервера"):
        super(ServerError, self).__init__(detail)


class Conflict(exceptions.APIException):
    status_code = status.HTTP_409_CONFLICT

    def __init__(self, detail="Запрос не может быть выполнен из-за конфликтного обращения к ресурсу."):
        super(Conflict, self).__init__(detail)


class ClientLimitError(exceptions.APIException):
    status_code = status.HTTP_428_PRECONDITION_REQUIRED

    def __init__(self, detail="Максимально можно запросить в одном запросе 100 записей!"):
        super(ClientLimitError, self).__init__(detail)


# noinspection PyUnresolvedReferences,PyArgumentList
class ExceptionResponse(Response):
    @property
    def rendered_content(self):
        if self.renderer_context.get('request').query_params.get('format', None) != 'html':
            self.accepted_renderer = JSONRenderer()
        ret = super(ExceptionResponse, self).rendered_content
        return ret
