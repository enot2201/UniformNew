from collections import namedtuple

from django.db import models
from django.http import QueryDict
from rest_framework.serializers import BaseSerializer


# noinspection PyUnresolvedReferences,PyArgumentList
class OwnedObjectSerializerMixin:
    """
    Записывает в поле указаное owner_field значение текущего пользователя который сделал запрос
    Example:

    class TopicSerializer(OwnedObjectSerializerMixin, ModelSerializer):
        class Meta(OwnedObjectSerializerMixin.Meta):
            owner_field = 'editor'
            model = Topic
    """
    class Meta:
        owner_field = 'owner'
        allow_rewrite = True
        foreign_key = False

    def to_internal_value(self, data):
        request = self.context['request']
        if self.instance is None or self.instance.id is None:
            if self.Meta.owner_field not in data or not self.Meta.allow_rewrite:
                data[self.Meta.owner_field] = request.user.id if self.Meta.foreign_key else request.user.username
        else:
            if self.Meta.owner_field in data and not self.Meta.allow_rewrite:
                del data[self.Meta.owner_field]
        return super().to_internal_value(data)


# noinspection PyUnresolvedReferences,PyArgumentList
class NestedSavingMixin:
    """
    В данный момент есть поддержка сохранения только связей один к одному
    Пример использования
    # todo-feature: Добавить поддержку сохранения foreign key
    class PersonalDataSerializer(ModelSerializer):
        class Meta:
            model = models.PersonalData
            fields = "__all__"

    class TeacherDetailSerializer(NestedSavingMixin, ModelSerializer):
        personal_data = PersonalDataSerializer() # Поле со связью один к одному
        class Meta:
            model = models.Teacher
            fields = "__all__"

    """

    def save(self, **kwargs):
        """
        Добавляем поддержку сохран/измен. персональнных данных преподавателя
        """
        self.pre_save()
        instance = super().save(**kwargs)
        self.post_save()
        return instance

    def pre_save(self):
        """
        Вызов перед сохранение корневого объекта
        Переопределить метод для задания определенной логики перед сохранением
        """

    def post_save(self, save_nested=True):
        """
        Вызов после сохранения корневого объекта
        """
        if save_nested:
            # Сохраняем после того как обработаем корневой объект
            self._save_nested_serializers()

    def is_valid(self, raise_exception=False):
        # Подготавливаем в этом месте т.к после выполнения функции is_valid()
        # будут отчищены лишнии данные(вложенные сериалайзеры)
        self._prepare_nested_data()
        # Страндартная валидация
        return super().is_valid(raise_exception)

    def _prepare_nested_data(self):
        """
        Подготовка вложенных данных
        Ищем все поля которые имеют базовый класс BaseSerializer
        Подготавливаем мета информацию о поле
        :return:
        """
        self._nested_data = []
        for f in self._writable_fields:
            if not isinstance(f, BaseSerializer):
                continue
            f_n = f.field_name
            # Получаем данные. Интересен только словарь
            if isinstance(self.initial_data, QueryDict):
                self.initial_data = dict(**self.initial_data)
            data = self.initial_data.pop(f_n, None)
            if not data or not isinstance(data, dict):
                continue
            # Сохраняем подготовленную структуру для будущего анализа как будет сохранять(все зависит от вида связи)
            self._append_nested_data({
                'data': data,
                '_meta': self._collention_info_field(f)
            })

    def _save_nested_serializers(self):
        """
        Анализирует подготовленные поля для сохранения и запускает необходимый обработчик сохранения поля
        в зависимости от типа связи
        """
        if not hasattr(self, '_nested_data'):
            raise RuntimeError("Вызовите функцию _prepare_nested_data "
                               "перед тем как будут отчищены не корректные данные! Например перед is_valid ")
        for nested_data in self._nested_data:
            # Получаем дистриптор поля
            related_field = getattr(self.instance, nested_data['_meta'].field_name)
            if not related_field:
                continue
            # Поле является связью OneToOne
            if isinstance(related_field, models.Model):
                # запускаем сохранение для связи OneToOne
                self._save_nested_one_to_one_field(nested_data)

    def _save_nested_one_to_one_field(self, nested_data_item: dict):
        """
        Обработчик сохранения
        :param nested_data_item:
            :key _meta: NamedTuple содержит всю мета информацию о поле вложенного сериалайзера
                        полученного ф-ией _collention_info_field
            :key data: dict данные которые были переданы в запросе
        """
        inst = self.instance
        meta = nested_data_item['_meta']
        # Бежим по полям ссылочной модели
        for _ in meta.related_model._meta.fields:
            r_model = _.related_model
            if not r_model:
                continue
            # Проверяем что поле является нужной моделью(связь O-0) именно на нужную модель
            if not issubclass(r_model, inst._meta.model):
                continue
            try:
                pk_val = inst.pk.hex
            except AttributeError as e:
                pk_val = inst.pk
            # Пытаемся получить инстант если есть(будет изменять)
            one_to_one_instance = getattr(inst, meta.field_name)
            nested_data_item['data'][_.name] = pk_val
            nest_serializer = meta.serializer_class(data=nested_data_item['data'], instance=one_to_one_instance,
                                                    partial=True)
            nest_serializer.is_valid(raise_exception=True)
            # Сохарняем или создаем новый
            nest_serializer.save()
            # Выходим
            break

    def _collention_info_field(self, field, extra_fields=None):
        """
        Сбор мета информации об поле
        :param field: Поле вложенного сериалайзера
        :param extra_fields: Расширенные поля
        :return:
        """
        f = field
        return self._build_nested_meta_class(extra_fields)(**{
            'field': f,
            'field_name': f.field_name,
            'related_model': f.Meta.model,
            'serializer_class': f.__class__,
        })

    def _build_nested_meta_class(self, extra_fields=None):
        """
        Строим именнованный tuple
        :param extra_fields: Поля которые будут добавлять стандарный набор полей
        :return: NamedTuple
        """
        if extra_fields is None:
            extra_fields = []
        fields = [
            "field", "field_name", "related_model",
            "serializer_class", *extra_fields,
        ]
        return namedtuple("Meta", fields)

    def _append_nested_data(self, data: dict):
        """
        Сохранения элемента с инфомрацией о вложенном сериалайзере в общий массив
        """
        self._nested_data.append(data)

