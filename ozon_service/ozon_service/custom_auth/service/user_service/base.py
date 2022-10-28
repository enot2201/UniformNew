from dataclasses import dataclass
from typing import Callable, Type

from loguru import logger
from django.db import transaction
from rest_framework.serializers import ModelSerializer
from modules.core.apps.custom_auth.service.data_type.create_type import *


@dataclass
class ActionRecord:
    """
    Контейнер для получаемых данных
    """
    action_type: str
    data_user: UserData | dict = None
    data_teacher: TeacherData | dict = None
    data_student: StudentData | dict = None
    data_university: UniversityData | dict = None
    data_department: DepartmentData | dict = None
    data_discipline: DisciplineData | dict = None
    data_discipline_teacher: DisciplinesTeacherData | dict = None
    data_teacher_department: TeacherDepartmentData | dict = None
    data_group: GroupData | dict = None

    def __post_init__(self):
        self.data_user = self.data_user and UserData(**self.data_user)
        self.data_teacher = self.data_teacher and TeacherData(**self.data_teacher)
        self.data_student = self.data_student and StudentData(**self.data_student)
        self.data_discipline_teacher = self.data_discipline_teacher and DisciplinesTeacherData(
            **self.data_discipline_teacher)
        self.data_university = self.data_university and UniversityData(**self.data_university)
        self.data_department = self.data_department and DepartmentData(**self.data_department)
        self.data_discipline = self.data_discipline and DisciplineData(**self.data_discipline)
        self.data_teacher_department = self.data_teacher_department and DisciplineData(**self.data_teacher_department)
        self.data_group = self.data_group and GroupData(**self.data_group)


@dataclass
class ActionRecordForDelete:
    """
    Контейнер для получения данных для удаления
    """
    action_type: str
    id: str


class ActionErrorType(RuntimeError):
    """
    Ошибка переданного типа
    """


class BaseUserService:
    ACTION_MAP = {
        'save_student': '_save_student_record',
        'save_user': '_save_user_record',
        'save_teacher': '_save_teacher_record',
        'save_university': '_save_university_record',
        'save_department': '_save_department_record',
        'save_group': '_save_group_record',
        'save_discipline': '_save_discipline_record',
        'save_teacher_department': '_save_teacher_department_record',
        'save_all_for_user': '_save_all_for_user_record',
        'save_all_for_teacher': '_save_all_for_teacher_record',
        'delete_user': '_delete_user_record',
    }
    PROCESS_TYPE_DELETE = 'delete'
    PROCESS_TYPE_UPDATE = 'update'
    PROCESS_TYPE_POST = 'post'

    def __init__(self, data: dict, process_type: str = PROCESS_TYPE_POST) -> None:
        self.process_type = process_type
        if process_type == self.PROCESS_TYPE_DELETE:
            self.action = ActionRecordForDelete(**data)
        else:
            self.action = ActionRecord(**data)

    def process(self):
        action = self.action.action_type
        handler = self._dispatch_handler(action)
        with transaction.atomic():
            logger.debug(f"Обработка создания записи:{action}. handler: {handler}")
            return handler()

    def _save_serializer(self, serializer_class: Type[ModelSerializer], data, instance=None):
        """
        Сохранить объект через сериалайзер
        """
        serializer = serializer_class(data=data, instance=instance)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return serializer

    def _dispatch_handler(self, name: str) -> (Callable, dict):
        """
        Получить метод обработки данных
        """
        value = self.ACTION_MAP.get(name)
        handler = getattr(self, value, None)
        if handler is None:
            raise ActionErrorType(f'Передан не допустимый тип {name}. '
                                  f'Допустимые типы действий: {"".join(self.ACTION_MAP.keys())}!')
        return handler
