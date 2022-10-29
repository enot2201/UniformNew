from threading import current_thread

import typing
from django.core.handlers.wsgi import WSGIRequest
from django.utils.deprecation import MiddlewareMixin

REQUESTS = {}


def get_current_request() -> typing.Union[WSGIRequest, None]:
    """
    Возвращает текущий запрос пользователя
    """
    thread = current_thread()
    if thread not in REQUESTS:
        return None
    return REQUESTS[thread]


class SetGlobalRequestMiddleware(MiddlewareMixin):
    """
    Промежуточный слой сохраняющий текущий запрос пользователя
    Запись текущего запроса(request)
    """

    def process_request(self, request):
        if hasattr(request, 'session'):
            request.session.clear()
        REQUESTS[current_thread()] = request
