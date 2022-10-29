from uuid import uuid4
from django.core.files import File
from django.contrib.auth.models import AbstractBaseUser
from django.utils import timezone
from django.db import models
from ..custom_auth.models import *

# s_learnMaterial = Schema('material')


class LearnMaterial(models.Model):
    id = models.UUIDField(default=uuid4, primary_key=True)
    name = models.CharField(db_column='name', verbose_name='Название дидактического материала', unique=False,
                            max_length=60)
    university = models.ForeignKey(University, models.CASCADE, related_name='material_university')
    teacher = models.ForeignKey(Teacher, models.CASCADE, related_name='material_teacher')
    file = models.FileField(upload_to='uploads/%Y/%m/%d/', verbose_name='Название Дидактического материала')
    type = models.CharField(db_column='type', verbose_name='Тип материала',max_length=60)
    disciplines = models.ForeignKey(Discipline, models.CASCADE,
                                    verbose_name='Дисциплина, к которой принадлежит дидактический материал')
    stGroup = models.ForeignKey(StudyGroup, models.CASCADE, related_name='material_StudyGroup')
