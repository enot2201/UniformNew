from dataclasses import dataclass
from .models import DangerLevel
from rest_framework.generics import get_object_or_404


@dataclass
class DataRecord:
    action_type: str = 'get_data'
    data: dict = None
    data_list: list = None


class DangerLevelService:
    ActionMap = {
        'get_data': '_get_data_record',
        'post_danger_data': '_post_danger_data_record',
        'update_danger_data': '_update_danger_data_record',
        'validate_danger_data': '_validate_danger_data_record',
    }
    MAX_DANGER_LEVEL = 100

    def __init__(self, data: dict):
        self._data = DataRecord(**data)

    def process(self):
        action = self._data.action_type
        handler = self.__dispatch_handler(action)
        return handler()

    def __dispatch_handler(self, name: str):
        """
        Получить метод обработки данных
        """
        value = self.ActionMap.get(name)
        handler = getattr(self, value, None)
        if handler is None:
            raise Exception(f'Передан не допустимый тип {name}. '
                            f'Допустимые типы действий: {"".join(self.ActionMap.keys())}!')
        return handler

    def _get_data_record(self):
        """
        Получение всех данных
        :return:
        """
        return DangerLevel.objects.all().values()

    def _post_danger_data_record(self):
        """
        Создание схемы для сопоставления уровня опасности данных
        :return:
        """
        danger_data = self._data.data
        new_data = {}
        for key, value in danger_data.items():
            DangerLevel.objects.create(name=key, danger_level=value)
            new_data.update({key: value})
        return new_data

    def _update_danger_data_record(self):
        """
        Обновление схемы для сопоставления уровня опасности данных
        :return:
        """
        updated_danger_data = self._data.data
        new_data = {}
        for danger_level in DangerLevel.objects.all():
            for key, value in updated_danger_data.items():
                if danger_level.name == key:
                    danger_level.danger_level = value
                    danger_level.save()
                    new_data.update({key: value})
                else:
                    continue
        return new_data

    def _validate_danger_data_record(self):
        """
        валидация по уровню опасности полученных данных
        :return:
        """
        fields = self._data.data_list
        new_data = []
        danger_level_data = {}
        danger_level_sum = 0
        i = 0
        danger_level_objects = DangerLevel.objects.filter(name__in=fields)
        for field in danger_level_objects:
            danger_level = field.danger_level
            danger_level_data.update({field: danger_level})
            danger_level_sum += danger_level
        danger_level_data_list = [(item, danger_level_data[item]) for item in danger_level_data]
        danger_level_data_list = sorted(danger_level_data_list, key=lambda x: x[1], reverse=True)
        while danger_level_sum > self.MAX_DANGER_LEVEL:
            new_data.append((danger_level_data_list[i][0]).name)
            danger_level_sum = danger_level_sum - danger_level_data_list[i][1]
            i += 1
        return new_data
