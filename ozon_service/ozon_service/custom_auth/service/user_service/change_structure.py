from datetime import datetime
from modules.core.apps.custom_auth.service.user_service.base import BaseUserService
from project_lib.rest.serializers import DynamicSerializerModel
from rest_framework.generics import get_object_or_404

from ...models import *

UserSerializer = DynamicSerializerModel(model=CustomUser).build()
StudentSerializer = DynamicSerializerModel(model=Student).build()
TeacherSerializer = DynamicSerializerModel(model=Teacher).build()
UniversitySerializer = DynamicSerializerModel(model=University).build()
DisciplineSerializer = DynamicSerializerModel(model=Discipline).build()
DepartmentSerializer = DynamicSerializerModel(model=Department).build()
GroupSerializer = DynamicSerializerModel(model=StudyGroup).build()
DisciplinesTeacherSerializer = DynamicSerializerModel(model=DisciplinesTeacher).build()
TeacherDepartmentSerializer = DynamicSerializerModel(model=TeacherDepartment).build()


class CreateStructureUser(BaseUserService):

    def _save_user_record(self):
        """
        Создание данных user
        """
        user_data = self.action.data_user
        data = dict(
            name=user_data.name,
            surname=user_data.surname,
            phone_number=user_data.phone_number,
            gender=user_data.gender,
            date_birth=user_data.date_birth,
            avatar_id=user_data.avatar_id,
        )
        if user_data.id:
            instance = CustomUser.objects.get(pk=user_data.id)
            return self._save_serializer(UserSerializer, data, instance).data
        return self._save_serializer(UserSerializer, data).data

    def _save_student_record(self, user_id: str = None, group_id: str = None):
        """
        Создание данных студента
        """
        student_data = self.action.data_student
        if user_id and group_id:
            data = dict(
                user=user_id,
                group=group_id,
                is_headman=student_data.is_headman,
            )
        else:
            if not student_data.user_id or not student_data.group_id:
                raise ValueError("При выборочном создании судента поля user_id и group_id являются обязательными")
            data = dict(
                user=student_data.user_id,
                group=student_data.group_id,
                is_headman=student_data.is_headman,
            )
        if student_data.id:
            instance = Student.objects.get(pk=student_data.id)
            return self._save_serializer(StudentSerializer, data, instance).data
        return self._save_serializer(StudentSerializer, data).data

    def _save_teacher_record(self, user_id: str = None):
        """
        Создание данных преподователя
        """
        teacher_data = self.action.data_teacher
        if user_id:
            data = dict(
                user_id=user_id,
                is_lead_department=teacher_data.is_lead_department
            )
        else:
            data = dict(
                user_id=teacher_data.user_id,
                is_lead_department=teacher_data.is_lead_department
            )
        if teacher_data.id:
            instance = Teacher.objects.get(pk=teacher_data.id)
            return self._save_serializer(TeacherSerializer, data, instance).data
        return self._save_serializer(TeacherSerializer, data).data

    def _save_university_record(self):
        """
        Создание данных yниверситета
        """
        university_data = self.action.data_department
        data = dict(
            name=university_data.name,
            city=university_data.city
        )
        if university_data.id:
            instance = University.objects.get(pk=university_data.id)
            return self._save_serializer(UniversitySerializer, data, instance).data
        return self._save_serializer(UniversitySerializer, data).data

    def _save_discipline_record(self):
        """
        Создание данных дисциплины
        """
        discipline_data = self.action.data_department
        data = dict(
            university=discipline_data.university,
            name=discipline_data.name,
        )
        if discipline_data.id:
            instance = Discipline.objects.get(pk=discipline_data.id)
            return self._save_serializer(DisciplineSerializer, data, instance).data
        return self._save_serializer(DisciplineSerializer, data).data

    def _save_department_record(self, university_id: str = None):
        """
        Создание данных кафедры
        """
        department_data = self.action.data_department
        if university_id:
            data = dict(
                university_id=university_id,
                name=department_data.name
            )
        else:
            data = dict(
                university_id=department_data.university_id,
                name=department_data.name
            )
        if department_data.id:
            instance = Department.objects.get(pk=department_data.id)
            return self._save_serializer(DepartmentSerializer, data, instance).data
        return self._save_serializer(DepartmentSerializer, data).data

    def _save_group_record(self, university_id: str = None):
        """
        Создание данных учебной группы
        """
        group_data = self.action.data_group
        if university_id:
            data = dict(
                university_id=university_id,
                name=group_data.name,
                course=group_data.course,
                type_education=group_data.type_education,
                direction=group_data.direction,
            )
        else:
            data = dict(
                university_id=group_data.university_id,
                name=group_data.name,
                course=group_data.course,
                type_education=group_data.type_education,
                direction=group_data.direction,
            )
        if group_data.id:
            instance = StudyGroup.objects.get(pk=group_data.id)
            return self._save_serializer(GroupSerializer, data, instance).data
        return self._save_serializer(GroupSerializer, data).data

    def _save_teacher_department_record(self, university_id: str = None):
        """
        Создание данных учебной группы
        """
        group_data = self.action.data_group
        if university_id:
            data = dict(
                university_id=university_id,
                name=group_data.name,
                course=group_data.course,
                type_education=group_data.type_education,
                direction=group_data.direction,
            )
        else:
            data = dict(
                university_id=group_data.university_id,
                name=group_data.name,
                course=group_data.course,
                type_education=group_data.type_education,
                direction=group_data.direction,
            )
        if group_data.id:
            instance = StudyGroup.objects.get(pk=group_data.id)
            return self._save_serializer(GroupSerializer, data, instance).data
        return self._save_serializer(GroupSerializer, data).data

    # def _save_all_record(self):
    #     """
    #     Создание всех обьектов связаных с user
    #     """
    #     user_id = None
    #     user_data = None
    #     soldier_service_data = None
    #     user_role_data = None
    #     soldier_data = None
    #     soldier = None
    #     if self.action.data_user:
    #         user_id = self.action.data_user.id
    #         user_data = self._save_user_record()
    #         if not user_id:
    #             user_id = get_object_or_404(CustomUser.objects.all(), username=self.action.data_user.username).id
    #     if self.action.data_soldier:
    #         soldier_data = self._save_soldier_record(user_id)
    #         soldier = soldier_data.serializer.instance.id
    #     if self.action.data_user_role:
    #         user_role_data = self._save_user_role_record(user_id)
    #     if self.action.data_soldier_service:
    #         soldier_service_data = self._save_soldier_service_record(soldier)
    #     return {
    #         'user': user_data,
    #         'user_role_data': user_role_data,
    #         'soldier': soldier_data,
    #         'soldier_service': soldier_service_data
    #     }

    def _delete_user_record(self):
        """
        Удаление User (подтягиваются остальные данные средствами Django)
        """
        user = get_object_or_404(CustomUser.objects.all().undeleted(), pk=self.action.id)
        user.delete()
