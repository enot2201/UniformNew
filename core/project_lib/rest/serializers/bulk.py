import inspect
from uuid import UUID

from rest_framework.exceptions import ValidationError
from rest_framework_bulk import BulkListSerializer


class BulkListSerializerFixUUID(BulkListSerializer):
    """
    Сериалайзер который исправляем получения объекта для изменения по ключу преобразовывая его в строку
    Исправление касается pk у модели с типом UUIDFIeld

    Пример использования:
    class ModelBulkSerializer(BulkSerializerMixin, serializers.ModelSerializer):
        class Meta:
            list_serializer_class = BulkListSerializerFixUUID
            model = Model1
            fields = '__all__'
    """

    def update(self, queryset, all_validated_data):
        id_attr = getattr(self.child.Meta, 'update_lookup_field', 'id')

        all_validated_data_by_id = {
            i.pop(id_attr): i
            for i in all_validated_data
        }

        if not all((bool(i) and not inspect.isclass(i)
                    for i in all_validated_data_by_id.keys())):
            raise ValidationError('')

        objects_to_update = queryset.filter(**{
            f'{id_attr}__in': all_validated_data_by_id.keys(),
        })

        if len(all_validated_data_by_id) != objects_to_update.count():
            raise ValidationError('Не найдены все объекты для обновления.')

        updated_objects = []

        for obj in objects_to_update:
            obj_id = getattr(obj, id_attr)
            if isinstance(obj_id, UUID):
                # Фикс получения данных по ключу через uuid
                obj_id = str(obj_id)
            obj_validated_data = all_validated_data_by_id.get(obj_id)

            updated_objects.append(self.child.update(obj, obj_validated_data))

        return updated_objects
