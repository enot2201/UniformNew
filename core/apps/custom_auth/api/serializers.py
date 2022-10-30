from rest_framework import serializers
from UniformNew.core.apps.custom_auth.models import CustomUser
from UniformNew.core.project_lib.rest.serializers import DynamicSerializerModel


class CustomUserSerializer(serializers.ModelSerializer):
    """
    Сериалайзер для работы с моделью CustomUser
    """

    class Meta:
        model = CustomUser
        fields = '__all__'


fields = '__all__,soldiers[__all__].service_records[__all__],role_users[__all__].role[id|name]'

