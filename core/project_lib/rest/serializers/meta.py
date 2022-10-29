import re
from collections import OrderedDict
from typing import Union, Type

from django.contrib.contenttypes.models import ContentType
from django.db.models.fields.related_descriptors import ReverseOneToOneDescriptor
from rest_framework import serializers
from rest_framework.utils.field_mapping import get_nested_relation_kwargs

from project_lib.rest.exceptions import BadRequestError
from .mixins import NestedSavingMixin


# noinspection PyUnresolvedReferences,PyArgumentList
class DynamicSerializerModel:
    """
    Динамический сериалайзер который может настраивать возвращаемые поля c вложенными обьектами
    Использование:
        # Все поля 1 ур
        DynamicSerializerModel(model=models.Teacher, attrs="__all__").build()
        # Все поля 1 ур и вложенный объект со всеми полями
        DynamicSerializerModel(model=models.Teacher, attrs="__all__,personal_data[__all__]").build()
        # Добавить реадктирование вложенного объекта со связью один к одному
        bases = [NestedSavingMixin]
        DynamicSerializerModel(model=models.Teacher, attrs="__all__,personal_data[__all__]").build(bases)
        # Добавить реадктирование вложенного объекта со связью один к одному и игнорить бланк поля
        bases = [NestedSavingMixin, IgnoreBlankSerializerMixin]
        DynamicSerializerModel(model=models.Teacher, attrs="__all__,personal_data[__all__]").build(bases)
        # Проброска extra_kwargs
        DynamicSerializerModel(model=models.Teacher, attrs="__all__").build(extra_kwargs_for_meta={'archivation_date': {'read_only': True}}))
    """
    NON_NULL = False  # исключать пустые поля из выборки

    def __init__(self, module_name=None, model_name=None, attrs="__all__", model=None):
        """
        !!!Важно, если вы хотите перечислить выборку цепную то не пишите так:
            rel1[__all__],rel1.rel2[__all__]
            Нужно писать так:
            rel1[__all__].rel2[__all__]
        :param module_name: Имя приложения где искать требуемую модель
        :param model_name: Имя модели в приложении module_name
        :param attrs: Атрибуты требуемых полей.
            Допустим есть модель User с полями
                - id
                - name
                - reg_date
            У пользователя есть история его действий - модель History(ссылка на модель Пользователь) c полями
                - id
                - user (related_name=histories, to=User)
                - action_type
                - date
            Имя модуля admin модель User:
                мы хотим получить все поля User:
                    - attrs = __all__
                мы хотим получить только требуемые поля User:
                    - attrs = id,name - Будет только 2 поля
                Если надо получить всю историю для User:
                    - attrs = id,histories[__all__] или id,histories[id|user|action_type|date]
                    Перечисленные поля в histories[...] это необходимые поля для выборки разделенные через символ |
                    Если бы была модель которая ссылается на History допустим RefHistory
                    То что бы получить информацию о пользователе его истории и инфу для каждой истории запрос будет
                    выглядить так:
                    __all__,histories[__all__].ref_histories_set[__all__]
                    __all__ - это первый уровень инфа пользака
                    .histories[__all__] - все поля истрии для каждого пользователя
                    .ref_histories_set[__all__] - для каждой истории пользователя вытягивает информацию для RefHistory
                    Пример структуры который вернется(это json просто лень кавышки и поля расписывать, а так везде ключ значение)
                    [
                        {
                            __all__, - поля которые есть в моделе пользователь
                            histories: [ - массив историй с детальной инфой о полях истории
                                         {  __all__, - поля которые есть у истории пользователя
                                            ref_histories_set: [
                                         }                       {__all__} - поля ref_histories_set
                                                               ] - 3 уровень(ref_histories_set[__all__])
                                       ] - 2 урвоень(histories[__all__])
                        } - 1 уровень(__all__)
                    ]

        """
        self.model = model or ContentType.objects.get(app_label=module_name, model=model_name.lower()).model_class()
        # Разбиваем если передали строку по ,
        if isinstance(attrs, str):
            attrs = attrs.split(",")
        # Убираем пробелы
        attrs = [w.strip() for w in attrs]
        self.builder = BuildNesteting(attrs)
        self.builder.parse()

    def build(self, extra_bases=None, extra_kwargs_for_meta=None) -> Type[serializers.ModelSerializer]:
        """
        Возвращает готовый сериалайзер
        :param extra_kwargs_for_meta: словарь, который будет добавлен в аттрибут extra_kwargs класса Meta
        :return:
        """
        root_fields = []
        fetch_field = []
        # Получаем поля первого уровня
        for field in self.builder.get_root():
            if field == "__all__":
                root_fields.extend(self.convert_all_predicat(self.model._meta.fields))
            else:
                root_fields.append(field)
        root_fields = self.fill_m2m_fieldname(root_fields)

        class BuildDynamicSerializer(self.__get_nested_serializer(extra_bases)):
            class Meta:
                model = self.model
                fields = root_fields
                childs = self.builder.get_nested()
                depth = self.builder.get_depth()
                fetch = fetch_field
                if extra_kwargs_for_meta:
                    extra_kwargs = extra_kwargs_for_meta

        return BuildDynamicSerializer

    @classmethod
    def convert_all_predicat(cls, fields) -> list:
        build = []
        for f in fields:
            build.append(f.name)
        return build

    def fill_m2m_fieldname(self, root_fields):
        """
        Заполняет именами полей для связей many to many
        """
        for f_name in self.builder.get_nested().keys():
            if list(filter(lambda x: x.name == f_name, self.model._meta.many_to_many)):
                root_fields.append(f_name)
        return list(set(root_fields))

    def __get_nested_serializer(self, extra_bases=None):
        """
        Рекурсивное создание сериалайзера с требуемыми полями
        """
        if extra_bases is None:
            extra_bases = []
        if not isinstance(extra_bases, (tuple, list)):
            extra_bases = [extra_bases]
        bases = []

        bases.extend(extra_bases)
        bases.append(serializers.ModelSerializer)

        class Nested(*bases):

            def to_representation(self, instance):
                return super().to_representation(instance)

            def build_unknown_field(self, field_name, model_class):
                """
                Вызываем ошибку о том когда передали неизвестное поле
                Выдаем информацию о допустимых полях.
                """

                related_names = []
                field_names = []
                error_message = OrderedDict()
                error_message['_detail'] = 'Имя поля `%s` не допустимо для модели `%s`.' % \
                                           (field_name, model_class.__name__)
                error_message['allow_related_names'] = related_names
                error_message['allow_field_names'] = field_names
                for f in model_class._meta.related_objects:
                    name = f.related_name
                    if not name:
                        name = "%s_set" % f.name
                    related_names.append(name)
                for f in model_class._meta.fields:
                    field_names.append(f.name)
                raise BadRequestError(
                    error_message

                )

            def build_nested_field(ser_self, field_name, relation_info, nested_depth):
                """
                Строитель вложенного сериалайзера с необходимыми полями
                """
                ALL = "__all__"  # Выборка всех полей
                root_fields = []  # Поля первого уровня
                child_field = {}  # Словарь с информацией о вложенных сериалайзерах
                try:
                    # Настройки сериалайзера
                    fields_list = ser_self.Meta.childs.get(field_name, [])
                    if not fields_list:
                        # Настроек нет, возвращаем обычное поле
                        return ser_self.build_relational_field(field_name, relation_info)
                    root_fields = fields_list
                    if isinstance(fields_list, dict):
                        root_fields = fields_list[self.builder.KEY_FIELDS]
                        childs = fields_list[self.builder.KEY_CHIELDS]
                        # инициализируем будущий сериалайзер информацией о вложеном
                        for i, key in enumerate(childs):
                            child = fields_list.get(key)
                            if child:
                                child_field[key] = child
                    finaly_root_fields = []
                    for field in root_fields:
                        if isinstance(field, str):
                            f_name = field
                            if f_name == ALL:
                                finaly_root_fields.extend(DynamicSerializerModel.convert_all_predicat(
                                    relation_info.related_model._meta.fields))
                            else:
                                finaly_root_fields.append(f_name)
                        else:
                            child_field.update(field)
                            finaly_root_fields.append(list(field.keys())[0])
                    # Убираем дубли
                    finaly_root_fields = list(set(finaly_root_fields))
                except Exception as e:
                    finaly_root_fields = ALL

                class NestedSerializer(Nested):
                    class Meta:
                        model = relation_info.related_model
                        depth = nested_depth - 1
                        fields = finaly_root_fields
                        childs = child_field

                field_class = NestedSerializer
                field_kwargs = get_nested_relation_kwargs(relation_info)
                try:
                    one_to_one_descriptor = getattr(ser_self.Meta.model, field_name)
                    if isinstance(one_to_one_descriptor, ReverseOneToOneDescriptor):
                        # Ищем есть ли примесь для вложенного редактирования
                        if list(filter(lambda x: x is NestedSavingMixin, ser_self.__class__.__mro__)):
                            # Есть - разрешаем редактирование
                            field_kwargs['read_only'] = False
                except AttributeError as e:
                    pass
                return field_class, field_kwargs

        return Nested


class BuildNesteting:
    REG = "(\w+)\[(.*)\]"  # парсин строку с "field[id|name] на имя и поля
    SPLITTER_ENUM_FIELDS = "|"  # разделитель для разделения вложенных имен полей
    SPLITTER_STR = ","  # Как разделять строку имен полей на первом уровне
    DOT = "."  # раздеитель вложенности

    KEY_FIELDS = '_fields'
    KEY_CHIELDS = '_childs'

    def __init__(self, attr: Union[list, str]) -> None:
        """
        Примерный формат attr:
        id,name,rel1[id].rel2[id|name],rel3[id|val1]
        :param attr:
        """
        if not isinstance(attr, (tuple, list)):
            attr = attr.split(self.SPLITTER_STR)

        self.attr = self.fix_list_attr(attr)
        self.root_fields = []
        self.default_depth = 1
        self.depth = self.default_depth
        super().__init__()

    def fix_list_attr(self, attr: list):
        """
        Исправляем когда передали массив строк вида
        ['id','name','rel1[__all__].rel2[__all__],simple_rel[__all__],simple_rel2[__all__]'
        Строка rel1[__all__].rel2[__all__],simple_rel[__all__],simple_rel2[__all__]
        преобразуется в макссив строк разделенный по запятой
        ['rel1[__all__].rel2[__all__]','simple_rel[__all__]','simple_rel2[__all__]']
        Потом удаляется из attr не корректная строка и мержится массив корректных строк
        :param attr: Список полей для парсинга
        """
        # Испраленные строки
        join_rel = []
        for i, f in enumerate(attr):
            splits = f.split(self.SPLITTER_STR)
            if len(splits) > 1:
                # Удаляем не корректную строку
                attr.pop(i)
                join_rel.extend(splits)
        attr.extend(join_rel)
        attr = set(attr)
        return attr

    def parse(self):
        if not hasattr(self, '_data'):
            self._data = {
                "_nested": self.__build_nested(fields=self.attr),
                "_root": list(set(self.root_fields)),
                "_depth": self.depth,
            }
        return self._data

    def get_root(self) -> list:
        """
        Получить поля 1 уровня
        """
        assert hasattr(self, "_data"), "Вызовите команду parse"
        return self._data['_root']

    def get_nested(self) -> dict:
        """
        Получить структуру иерархии
        """
        assert hasattr(self, "_data"), "Вызовите команду parse"
        return self._data['_nested']

    def get_depth(self) -> int:
        """
        Получить глубину вложености
        """
        assert hasattr(self, "_data"), "Вызовите команду parse"
        return self._data['_depth']

    def _parse_fields(self, string, is_name=False):
        """
        Разбор строки на имя поля и его наборе полей
        :param string: Строка формата rel1[id|name|val]
        :param is_name: если указан флаг возвращает только имя поля если подходит под шаблон REG
                        иначе вернет переданную строку
        """
        if not string:
            return None
        reg_str = re.findall(self.REG, string)
        if reg_str:
            if is_name:
                return reg_str[0][0]
            return reg_str[0]
        if is_name:
            return string

    def __build_nested(self, fields):
        """
        Разбор полей и передача их в функцию для формирования вложеной структуры
        с информацией о полях и детях
        :param fields: перечень полей
        :return:
        """
        root = None
        nested_level_fields = {}
        _tmp = [self.default_depth]
        for field in fields:
            parse = self._parse_fields(field)
            if parse and not root:
                root = parse[0]
            # if parse and len(field.split(self.DOT)) == 1:
            #     root = None
            if parse:
                # Разбиваем поля на уровни вложенности
                fields_dot = field.split(self.DOT)
                _tmp.append(len(fields_dot))
                self.__recurse_build_node(root, fields_dot, nested_level_fields)
                # ПОсле отработки добавили в рутовый набор полей сериалайзера 1 уровня
                self.root_fields.append(root)
                # Рекурсия отработала, сбрасываем рута, т.к больше нет детей
                root = None
            else:
                # Поля первого уровня
                self.root_fields.append(field)
                continue
        self.depth = max(_tmp)
        return nested_level_fields

    def __recurse_build_node(self, node_name: str, fields: list,
                             obj: dict = None, depth: int = None) -> dict:
        """
        рекурсивное формирование структуры
        :param node_name: Имя узла
        :param fields: Список полей
        :param obj: Объект для которого формируется, по умолчанию создается пустой
        :param depth: Глубина вложенности, по умолчанию 1
        :return: Структура
        """
        if depth is None:
            depth = self.default_depth
        if obj is None:
            obj = {}
        for field in fields:
            root_name = self._parse_fields(field, is_name=True)
            node = obj.get(root_name)
            if not node:
                # Стром структуру по умолчанию
                node = self._init_node(root_name, obj)
            parse_fields = self._parse_fields(field)
            if parse_fields:
                node[self.KEY_FIELDS].extend(parse_fields[1].split(self.SPLITTER_ENUM_FIELDS))
            if len(fields) > 1:
                child_name = self._parse_fields(fields[1], is_name=True)
                node[self.KEY_CHIELDS].append(child_name)
                node[self.KEY_FIELDS].append(child_name)
                if depth == 1:
                    self.root_fields.append(root_name)
            self.node_unique_fields(node)
            fields.pop(0)

            depth += 1
            self.__recurse_build_node(node_name, fields, node, depth)
        return obj

    def _init_node(self, key_name: str, obj: dict) -> dict:
        """
        Сформировать начальную структуру узла для объекта
        :param key_name: имя будущего ключа
        :param obj: ссылка на объект для которого нужно прекрипить узел
        :return: Новый узел
        """
        obj[key_name] = {
            self.KEY_FIELDS: [],
            self.KEY_CHIELDS: [],
            self.KEY_CHIELDS: [],
        }
        return obj[key_name]

    def node_unique_fields(self, node: dict):
        """
        Убираем дублируемые имена
        :param node: Узел
        """
        node[self.KEY_FIELDS] = list(set(node[self.KEY_FIELDS]))
        node[self.KEY_CHIELDS] = list(set(node[self.KEY_CHIELDS]))
