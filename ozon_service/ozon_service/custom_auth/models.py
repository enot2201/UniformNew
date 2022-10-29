from uuid import uuid4

from django.contrib.auth.models import AbstractBaseUser
from django.utils import timezone
from django.db import models


class University(models.Model):
    id = models.UUIDField(default=uuid4, primary_key=True)
    name = models.CharField(db_column='name', verbose_name="название учебного заведения", max_length=60, unique=False)
    city = models.CharField(db_column='city', verbose_name="город", max_length=50, unique=False)


class CustomUser(models.Model):
    USERNAME_FIELD = 'username'
    password = None
    last_login = None
    choices = (("male", "мужчина"), ("female", "женщина"))

    id = models.UUIDField(default=uuid4, primary_key=True)
    gender = models.CharField(db_column='gender', choices=choices, verbose_name="пол", max_length=10, null=True,
                              unique=False)
    date_birth = models.DateTimeField(db_column='date_birth', verbose_name="День рождения", null=True, blank=True)
    phone_number = models.CharField(db_column='phone_number', verbose_name="номер телефона", max_length=18, null=True,
                                    unique=True)
    name = models.CharField(db_column='name', verbose_name="имя", max_length=20, null=True, unique=False)
    avatar = models.ImageField(db_column="avatar", verbose_name="Аватарка пользователя", null=True)
    surname = models.CharField(db_column='surname', verbose_name="фамилия", max_length=20, null=True, unique=False)


class Student(models.Model):
    choices = (
        ("classic", 'обычная степендия'), ('increased', 'повышенная степендия'))
    id = models.UUIDField(default=uuid4, primary_key=True)
    user_id = models.ForeignKey('CustomUser', models.CASCADE, related_name='user_user')
    group = models.ForeignKey('StudyGroup', models.CASCADE, related_name='role_unit_roles')
    is_headman = models.BooleanField(default=False, verbose_name='Признак старосты', null=True)
    grant = models.CharField(default=False, db_column='grants', verbose_name="степендия",
                             max_length=60)
    exam_points = models.SmallIntegerField(db_column='exam_points', verbose_name="баллы за экзамен", unique=False)


class Teacher(models.Model):
    id = models.UUIDField(default=uuid4, primary_key=True)
    user_id = models.ForeignKey('CustomUser', models.CASCADE, related_name='teacher_user')
    groups = models.ForeignKey('StudyGroup', models.CASCADE, related_name='teacher_group')
    department = models.CharField(db_column='department', verbose_name="кафедра", max_length=20, unique=False)
    is_lead_department = models.BooleanField(default=False, verbose_name='Признак председателя кафедры', null=True)


class Discipline(models.Model):
    university = models.ForeignKey('University', models.CASCADE, related_name='discipline_university')
    id = models.UUIDField(default=uuid4, primary_key=True)
    name = models.CharField(db_column='name', verbose_name="название дисциплины", max_length=60, unique=True)


class Department(models.Model):
    id = models.UUIDField(default=uuid4, primary_key=True)
    university = models.ForeignKey('University', models.CASCADE, related_name='department_university')
    name = models.CharField(db_column='name', verbose_name="название кафедры", max_length=60, unique=True)


class DisciplinesTeacher(models.Model):
    id = models.UUIDField(default=uuid4, primary_key=True)
    discipline = models.ForeignKey('Discipline', models.CASCADE, related_name='teacher_disciplines')
    teacher = models.ForeignKey('Teacher', models.CASCADE, related_name='disciplines_teachers')


class StudentsGroups(models.Model):
    id = models.UUIDField(default=uuid4, primary_key=True)
    group = models.ForeignKey('StudyGroup', models.CASCADE, related_name='student_group')
    student = models.ForeignKey('Student', models.CASCADE, related_name='group_student')


class TeacherDepartment(models.Model):
    id = models.UUIDField(default=uuid4, primary_key=True)
    teacher = models.ForeignKey('Teacher', models.CASCADE, related_name='teacher_department')
    department = models.ForeignKey('Department', models.CASCADE, related_name='department_teacher')


class StudyGroup(models.Model):
    type_education_choices = (
        ("magistracy", "магистратура"), ("undergradute", "бакалавриат"), ("specialis", "специалитет"))
    id = models.UUIDField(default=uuid4, primary_key=True)
    university = models.ForeignKey('University', models.CASCADE, related_name='group_university')
    name = models.CharField(db_column='name', verbose_name="название группы", max_length=60, unique=False)
    course = models.SmallIntegerField(db_column='course', verbose_name="курс", unique=False)
    type_education = models.TextField(db_column='type_eduction', choices=type_education_choices, unique=False,
                                      verbose_name="тип образования", max_length=60)
    direction = models.CharField(db_column='direction', unique=False, verbose_name="направление", max_length=60)
