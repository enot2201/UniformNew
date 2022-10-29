from collections import OrderedDict
from math import ceil

from django.core.paginator import InvalidPage, Page, EmptyPage, PageNotAnInteger
from django.utils.functional import cached_property
from rest_framework.exceptions import NotFound
from rest_framework.pagination import BasePagination
from rest_framework.response import Response

from .exceptions import ClientLimitError
from .views.mixins import FilterListMixin


def _positive_int(integer_string, strict=False, cutoff=None):
    ret = int(integer_string)
    if ret < 0 or (ret == 0 and strict):
        raise ValueError()
    if cutoff:
        ret = min(ret, cutoff)
    return ret


class LimitOffsetPagination(BasePagination):
    """
    Пагинация ответа limit/offset based style.

    http://api.example.org/accounts/?limit=100
    http://api.example.org/accounts/?offset=400&limit=100

    Пример: http://100.100.100.30:18070/pages/viewpage.action?pageId=29953243
    """
    default_limit = 100
    limit_query_param = 'limit'
    offset_query_param = 'offset'
    max_limit = 100

    def __init__(self):
        self.count = 0
        super(LimitOffsetPagination, self).__init__()

    def check_raise_limit_max(self, limit, count):
        """
        Вызов ошибки при запросе более 100 записей
        :param limit: Лимит записей
        :param count: Количество записей в БД всего
        :return:
        """
        if limit:
            # Если лимит больше 101 и количество записей в бд больше максимального лимита вызваем ошибку
            # Т.к нет смысла вызывать ошибку если в бд записей меньше 101
            if limit >= self.max_limit + 1 and count >= self.max_limit + 1:
                raise ClientLimitError()
        # Нет смысла вызывать ошибку если не передали лимит и в бд записей меньше 101
        elif count >= self.max_limit + 1:
            raise ClientLimitError()

    def paginate_queryset(self, queryset, request, view=None):
        limit = self._get_limit(request)
        offset = self._get_offset(request)
        self.count = self._get_count(queryset)
        # Если не используется фильтрация проверяем лимит ответа
        if not request.query_params.get(FilterListMixin.query_filter_param):
            self.check_raise_limit_max(limit, self.count)
        if limit is None:
            if offset == 0:
                return queryset
            return list(queryset[offset:])
        else:
            return list(queryset[offset:offset + limit])

    def get_paginated_response(self, data):
        """
        Вернуть сформированый ответ сервера
        :param data:
        :return:
        """
        return Response(OrderedDict([
            ('count', self.count),
            ('results', data)
        ]))

    def _get_limit(self, request):
        # при наличии фильтров лимит либо берется из запроса либо отсутствует
        if request.query_params.get(FilterListMixin.query_filter_param):
            if request.query_params.get(self.limit_query_param):
                try:
                    return _positive_int(request.query_params.get(self.limit_query_param))
                except (KeyError, ValueError):
                    return None
            return None
        # без фильтров есть лимит по умолчанию на случай отсутствия его в запросе
        if self.limit_query_param:
            try:
                return _positive_int(
                    request.query_params.get(self.limit_query_param, 100),
                )
            except (KeyError, ValueError):
                pass
        return self.default_limit

    def _get_offset(self, request):
        try:
            return _positive_int(request.query_params[self.offset_query_param])
        except (KeyError, ValueError):
            return 0

    def to_html(self):
        return ''

    @staticmethod
    def _get_count(queryset):
        """
        Количество записей
        """
        try:
            return queryset.total_count()
        except (AttributeError, TypeError):
            return len(queryset)


class QuerySetPaginator:
    """
    Обертка QuerySet в блоки в виде страниц с количеством объектов на странице
    """

    def __init__(self, queryset, per_page):
        """
        :param queryset: QuerySet для пагинации страниц
        :param per_page: количество инстансов на тсранице
        """
        self.queryset = queryset
        if per_page is None:
            per_page = 0
        self.per_page = int(per_page)

    def init_page(self, number):
        """Вернуть страницу(сформированный QuerySet) по номеру"""
        if not self.per_page:
            return self._get_page(self.queryset, self.per_page, self)
        number = self.get_valid_num(number)
        bottom = (number - 1) * self.per_page
        top = bottom + self.per_page
        if top >= self.total_count:
            top = self.total_count
        return self._get_page(self.queryset[bottom:top], number, self)

    def _get_page(self, *args, **kwargs):
        """
        Инстанс страницы
        """
        return Page(*args, **kwargs)

    def get_valid_num(self, number: str):
        """Валидация номера страницы"""
        try:
            if isinstance(number, float) and not number.is_integer():
                raise ValueError
            number = int(number)
        except (TypeError, ValueError):
            raise PageNotAnInteger('Ожидалось целое число')
        if number < 1:
            raise EmptyPage('Страница не может быть меньше 1')
        if number > self.total_pages and self.total_pages:
            raise EmptyPage('Конец страниц')
        return number

    @cached_property
    def total_count(self):
        """Количество записей в БД(всего)."""
        try:
            return self.queryset.total_count()
        except (AttributeError, TypeError):
            return len(self.queryset)

    @cached_property
    def total_pages(self):
        """Количество страниц всего"""
        if self.total_count == 0 or self.per_page == 0:
            return 0
        hits = max(1, self.total_count)
        return ceil(hits / self.per_page)


class PageNumberPagination(BasePagination):
    """
    Постраничный пагинатор ответа сервера
    Для перехода по страницам используется параметр запроса ?page
    Для задания количества записей на странице используется параметр запроса ?per_page
    http://ex.ru?page=2&per_page=25 - 2 страница с 25 записями
    http://ex.ru?page=3&per_page=25 - 3 страница с 25 записями
    http://ex.ru?page=3&per_page=10 - 3 страница с 10 записями
    """
    page_size_query_param = 'per_page'
    page_query_param = 'page'
    max_page_size = None
    page_size = 100

    def is_filter(self, request):
        return request.query_params.get(FilterListMixin.query_filter_param)

    def get_size_for_page(self, request):
        """
        Вернуть количество записей на одной странице если не задан параметр параметра запроса выводит page_size
        """
        if self.is_filter(request):
            # при фильтрации если не передан параметр размера страницы - возвращаем всё, размер по умолчанию отсутствует
            self.page_size = None

        if self.page_size_query_param:
            try:
                return _positive_int(
                    request.query_params[self.page_size_query_param],
                    strict=True,
                    cutoff=self.max_page_size
                )
            except (KeyError, ValueError):
                pass

        return self.page_size

    def paginate_queryset(self, queryset, request, view=None):
        """Обработка пагинации QuerySet"""
        size = self.get_size_for_page(request)

        paginator = QuerySetPaginator(queryset, size)
        page_number = request.query_params.get(self.page_query_param, 1)

        try:
            self.page = paginator.init_page(page_number)
        except InvalidPage as e:
            raise NotFound("Страница не найдена.")

        self.request = request
        return list(self.page)

    def get_paginated_response(self, data):
        """Вернуть сформированный ответ"""
        return Response(OrderedDict([
            ('page', self.page.number),  # Номер текущей страницы
            ('per_page', self.get_size_for_page(self.request)),  # Колияество элементов допустимое на странице
            ('total_pages', self.page.paginator.total_pages),  # Всего страниц(количество)
            ('total_items', self.page.paginator.total_count),  # Всего записей в БД
            ('current_count_page', len(data)),  # Количество на странице(в данный момент)
            ('results', data)  # Результат
        ]))

    def to_html(self):
        return ''
