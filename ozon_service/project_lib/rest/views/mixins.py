from django.db import transaction
from loguru import logger
from django.db.models.query import QuerySet


from project_lib.db.models import DeletedQuerySet
from project_lib.db.query import QFilter
from project_lib.db.query.lookupy import Collection

__GLOB_DynamicSerializerModel = None


def GetDynamicSerializerModel():
    """Сокращение локлаьного импорта DynamicSerializerModel до 1 раза"""
    global __GLOB_DynamicSerializerModel
    if __GLOB_DynamicSerializerModel is None:
        from project_lib.rest.serializers import DynamicSerializerModel
        __GLOB_DynamicSerializerModel = DynamicSerializerModel
    return __GLOB_DynamicSerializerModel

# noinspection PyUnresolvedReferences,PyArgumentList
class FilterListMixin:
    """
    Фильтрация из параметров запроса
    Пример использования - http://100.100.100.30:18070/pages/viewpage.action?pageId=29953236
    Список предикатов
        exact - Точное совпадение.
        iexact - Регистронезависимое точное совпадение.
        contains - Регистрозависимая проверка на вхождение.
        icontains - Регистронезависимая проверка на вхождение.
        in - Проверяет на вхождение в список значений.
        gt - Больше чем.
        gte - Больше чем или равно.
        lt - Меньше чем.
        lte - Меньше чем или равно.
        startswith - Регистрозависимая проверка начинается ли поле с указанного значения.
        istartswith - Регистронезависимая проверка начинается ли поле с указанного значения.
        endswith - Регистрозависимая проверка оканчивается ли поле с указанного значения.
        iendswith - Регистронезависимая проверка оканчивается ли поле с указанного значения.
        range -Проверка на вхождение в диапазон (включающий).
        year - Проверка года
        month - Проверка месяца
        day - Проверка дня
        week_day - Проверка дня недели
        hour - Проверка часа
        minute - Проверка минут
        second - Проверка секунд
        isnull - Принимает True или False
        words- Поиск по словам
    ОПЕРАТОРЫ
        {AND} - логическое И
        {OR} - логическое ИЛИ
    Использование:
        >>>
        >>> from rest_framework.viewsets import ModelViewSet
        >>>
        >>>
        >>> class ViewSet(FilterListMixin, ModelViewSet):
        >>>     queryset = models.Model.objects.all()
        >>>     serializer_class = serializers.ModelSerializer
    """
    DISTINCT = True
    query_distinct_param = 'distinct'
    query_filter_param = 'filter'

    def filter_queryset(self, queryset: QuerySet) -> QuerySet:
        filter_strings = self.request.GET.get(self.query_filter_param)
        if filter_strings:
            if isinstance(queryset, (QuerySet, DeletedQuerySet)):
                queryset = queryset.filter(
                    QFilter.query_filter(filter_strings))
            elif isinstance(queryset, list):
                queryset = list(Collection(queryset).filter(
                    QFilter.list_filter(filter_strings)))

        s = super(FilterListMixin, self)
        if hasattr(s, 'filter_queryset'):
            queryset = s.filter_queryset(queryset)
        if isinstance(queryset, QuerySet) and self.DISTINCT:
            distinct_strings = self.request.GET.get(self.query_distinct_param)
            if distinct_strings:
                fields = distinct_strings.split(',')
                queryset = queryset.distinct(*fields)
            else:
                queryset = queryset.distinct()
        return queryset


# noinspection PyUnresolvedReferences,PyArgumentList
class OrderListMixin:
    """
    Сортировка queryset по параметру "order" в запросе url
    ?order=field_name по возрастанию
    ?order=-field_name по убыванию из-за символа "-" перед именем поля
    ?order=-field_name1,-field_name2 сортировка по двум полям
    Использование:
    >>>
    >>> from rest_framework.viewsets import ModelViewSet
    >>>
    >>>
    >>> class ViewSet(OrderListMixin, ModelViewSet):
    >>>     queryset = models.Model.objects.all()
    >>>     serializer_class = serializers.ModelSerializer
    """
    SORT_PARAM_NAME = 'order'

    def filter_queryset(self, queryset):
        if isinstance(queryset, QuerySet):
            s = super(OrderListMixin, self)
            if hasattr(s, 'filter_queryset'):
                queryset = s.filter_queryset(queryset)
            order_field = self.request.GET.get(self.SORT_PARAM_NAME)
            if order_field:
                queryset = queryset.order_by(*order_field.split(','))
        return queryset


# noinspection PyUnresolvedReferences,PyArgumentList
class AtomicMixin:
    """
    Миксин выполняющий каждый "Опасный" запрос внутри блока транзакций, в случаи ошибки делает rollback
        >>> from rest_framework.viewsets import ModelViewSet
        >>>
        >>>
        >>> class ViewSet(AtomicMixin, ModelViewSet):
        >>>     queryset = models.Model.objects.all()
        >>>     serializer_class = serializers.ModelSerializer
    """

    def dispatch(self, request, *args, **kwargs):
        if request.method == "GET":
            return super(AtomicMixin, self).dispatch(request, *args, **kwargs)
        # Опасный запрос - POST, PUT ...
        with transaction.atomic():
            return super(AtomicMixin, self).dispatch(request, *args, **kwargs)

    def handle_exception(self, *args, **kwargs):
        response = super(AtomicMixin, self).handle_exception(*args, **kwargs)

        if getattr(response, 'exception') and self.request.method != "GET":
            transaction.set_rollback(True)

        return response


# noinspection PyUnresolvedReferences,PyArgumentList
class SerializerViewSetMixin:
    """
    Примись собирающая сериалайзер на основе модели queryset
    Добавляет query параметр из строки запроса:
        - select_fields - строка в формате атрибуатов для генерации см. документацию DynamicSerializerModel

    Пример:
    class TestReferenceViewSet(SerializerViewSetMixin, ModelViewSet):
        queryset = models.TestReference.objects.undeleted()
    """
    serializer_fields = "__all__"
    query_param_fields_name = "select_fields"

    def __new__(cls, *args, **kwargs):
        """
        Начальноая инициализация дефолтного сериалайзера полями указанными в serializer_fields
        при создании класса
        """
        # Если не задан сериалайзер, но указан queryset в классе наследнике - генерируей класс
        if getattr(cls, 'serializer_class', None) is None \
                and getattr(cls, 'queryset', None) is not None:
            DynamicSerializerModel = GetDynamicSerializerModel()
            default_cls_serializer = DynamicSerializerModel(model=cls.queryset.model,
                                                            attrs=cls.serializer_fields).build()
            default_cls_serializer.__name__ = "%s%s" % (cls.__name__, default_cls_serializer.__name__)
            cls.serializer_class = default_cls_serializer
        return super().__new__(cls)

    def get_serializer(self, queryset=None, field_name=None, *args, **kwargs):
        """
        :param queryset: QuerySet
        :param field_name: Имена полей для формирования сериалайзера
        """
        from rest_framework.generics import GenericAPIView
        assert issubclass(self.__class__,
                          GenericAPIView), "Ожидался наследник от rest_framework.generics.GenericAPIView"
        assert hasattr(self, 'queryset'), "Не указано атрибут queryset у класса %s" % self.__class__
        field_name = self.request.query_params.get(self.query_param_fields_name, field_name)
        if field_name is None:
            field_name = field_name or self.serializer_fields
        # Строим новый сериалайзер т.к поля изменились
        if self.serializer_fields != field_name:
            DynamicSerializerModel = GetDynamicSerializerModel()
            self.serializer_class = DynamicSerializerModel(model=self.queryset.model, attrs=field_name).build()
        if kwargs and queryset is None:
            instance = kwargs.pop('instance', None)
            if instance:
                queryset = instance
        return super().get_serializer(queryset, *args, **kwargs)
