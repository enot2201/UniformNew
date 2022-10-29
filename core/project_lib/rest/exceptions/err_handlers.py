from django.conf import settings
from django.core.exceptions import PermissionDenied, FieldError
from django.db.models import ProtectedError
from django.http import Http404
from loguru import logger
from rest_framework.exceptions import ErrorDetail
from rest_framework.utils.serializer_helpers import ReturnList
from rest_framework.views import set_rollback

from .errors import *


def _get_recursive_error_strings(item, error_strings=None):
    if not error_strings:
        error_strings = list()
    if isinstance(item, ErrorDetail):
        error_strings.append(item)
    elif isinstance(item, list):
        for i in item:
            error_strings = _get_recursive_error_strings(i, error_strings)
    elif isinstance(item, dict):
        for i in item.values():
            error_strings = _get_recursive_error_strings(i, error_strings)
    return error_strings


# noinspection PyUnresolvedReferences,PyArgumentList
def exception_handler(exc: ApiException, context: dict):
    """
    Возвращает обработаную ошибку с корректным статусов ответа сервера
    :param exc: ошибка наследуемая от ApiException
    :param context: Контекст запроса
    :return:
    """
    # В случае, когда detail представляет из себя список - объединяем его
    if hasattr(exc, 'detail') and isinstance(exc.detail, ReturnList):
        strings = _get_recursive_error_strings(exc.detail)
        merged_detail = {'_detail': ErrorDetail(string='; '.join(strings))}
        exc.detail = merged_detail

    if settings.DEBUG:
        logger.exception(context)
    if context.get('request').query_params.get('format', None) == 'html':
        content_type = "text/html; charset=utf-8"
    else:
        content_type = "application/json; charset=utf-8"
    if isinstance(exc, exceptions.APIException):
        headers = {}
        if getattr(exc, 'auth_header', None):
            headers['WWW-Authenticate'] = exc.auth_header
        if getattr(exc, 'wait', None):
            headers['Retry-After'] = '%d' % exc.wait

        if isinstance(exc.detail, dict):
            data = exc.detail
        elif isinstance(exc.detail, list):
            data = exc.detail
        else:
            data = {'_detail': exc.detail}

        set_rollback()
        return ExceptionResponse(data, status=exc.status_code, headers=headers, content_type=content_type)
    elif isinstance(exc, FieldError):
        # Пытаемся проверить не примещана ли миксина открывюащая доступ к фильтру
        from ..views import FilterListMixin
        is_search_mixin = list(
            filter(
                # Ищем в наследовании вьюхии упоминания о возможности фильтрации
                lambda x: x is FilterListMixin, context['view'].__class__.__mro__
            )
        )
        if not is_search_mixin:
            # не найдена смиксина, видимо ошибка на сервере
            set_rollback()
            data = {"_detail": exc.args[0]}
            return ExceptionResponse(data, status=status.HTTP_500_INTERNAL_SERVER_ERROR, content_type=content_type)
        # Ошибку вызвал клиент, валидирует и информируем клиента
        from django.db.models import Field
        msg = exc.args[0]
        # Проверка что ошибка является не известнымм lookup filter djnago
        if msg.startswith('Unsupported'):
            info_url = "http://100.100.100.30:18070/pages/viewpage.action?pageId=29953236"
            msg = {"allow_lookups": list(Field.class_lookups.keys()), "url_detal_info": info_url}
        set_rollback()
        data = {"_detail": msg}
        return ExceptionResponse(data, status=status.HTTP_400_BAD_REQUEST, content_type=content_type)
    elif isinstance(exc, ValueError):
        set_rollback()
        data = {"_detail": exc.args[0]}
        return ExceptionResponse(data, status=status.HTTP_400_BAD_REQUEST, content_type=content_type)
    elif isinstance(exc, Http404):
        set_rollback()
        data = {"_detail": "Объект не найден."}
        return ExceptionResponse(data, status=status.HTTP_404_NOT_FOUND, content_type=content_type)

    elif isinstance(exc, PermissionDenied):
        set_rollback()
        data = {"_detail": "Недостаточно прав."}
        return ExceptionResponse(data, status=status.HTTP_403_FORBIDDEN, content_type=content_type)
    elif isinstance(exc, ProtectedError):
        set_rollback()
        data = {"_detail": exc.args[0]}
        return ExceptionResponse(data, status=status.HTTP_409_CONFLICT, content_type=content_type)

    msg = str(getattr(exc, 'message', exc))
    data = {"_detail": msg}
    if not settings.DEBUG:
        logger.exception(context)
    return ExceptionResponse(data, status=status.HTTP_500_INTERNAL_SERVER_ERROR, content_type=content_type)
