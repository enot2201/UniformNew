from django.db import models


class DangerLevel(models.Model):
    """
    сопоставление поля и предание ему уровня опассности
    """
    name = models.CharField(unique=True, max_length=50)
    danger_level = models.SmallIntegerField()
