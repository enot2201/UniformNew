from rest_framework import exceptions
from rest_framework.metadata import SimpleMetadata
from rest_framework.exceptions import PermissionDenied
from rest_framework.request import clone_request
from django.http.response import Http404


class ReadOnlyViewMetaData(SimpleMetadata):
    """
    Добавляет обработку получения options для "безопасных" методов в блок actions

    Пример:
    class ReadOnlyView(ListAPIView, GenericViewSet):
        queryset = ...
        serializer_class = ...
        metadata_class = ReadOnlyViewMetaData

    """

    def determine_actions(self, request, view):
        actions = {}
        for method in {'GET'} & set(view.allowed_methods):
            view.request = clone_request(request, method)
            try:
                if hasattr(view, 'check_permissions'):
                    view.check_permissions(view.request)

            except (exceptions.APIException, PermissionDenied, Http404):
                pass
            else:

                serializer = view.get_serializer()
                actions[method] = self.get_serializer_info(serializer)
            finally:
                view.request = request

        return actions
