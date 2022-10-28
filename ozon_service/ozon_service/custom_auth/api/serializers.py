from rest_framework import serializers
from modules.core.apps.custom_auth.models import CustomUser
from project_lib.rest.serializers import DynamicSerializerModel


class CustomUserSerializer(serializers.ModelSerializer):
    """
    Сериалайзер для работы с моделью CustomUser
    """

    class Meta:
        model = CustomUser
        fields = '__all__'


fields = '__all__,soldiers[__all__].service_records[__all__],role_users[__all__].role[id|name]'


class DetailUserSerializer(DynamicSerializerModel(model=CustomUser, attrs=fields).build()):

    def to_representation(self, instance):
        data = super().to_representation(instance)
        soldiers = data.pop('soldiers', None)
        roles = data.pop('role_users', None)
        data.setdefault('soldier', None)
        data.setdefault('role', None)
        if soldiers:
            soldier = soldiers[0]
            record = soldier.pop("service_records")
            soldier['service_record'] = None
            if record:
                soldier |= {
                    'service_record': record[0]
                }
            data['soldier'] = soldier
        if roles:
            role = roles[0]
            role_name = role.pop('role')
            role['name'] = role_name['name']
            role['role_id'] = role_name['id']
            data['role'] = role
        return data
