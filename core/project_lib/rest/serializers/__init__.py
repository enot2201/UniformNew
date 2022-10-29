from .meta import DynamicSerializerModel
from .mixins import NestedSavingMixin, OwnedObjectSerializerMixin

try:
    from rest_framework_bulk import BulkListSerializer
    from .bulk import BulkListSerializerFixUUID
except ImportError as e:
    from loguru import logger
    msg = "BulkListSerializerFixUUID не поддерживается. Пакет rest_framework_bulk не установлен"
    logger.warning(msg)

    def raise_err(*args, **kwargs):
        raise RuntimeError(msg)

    BulkListSerializerFixUUID = raise_err
