# @crtinfo: Ифно
from django.http import HttpResponse



def binary_response(data, report_name, conten_type="odt"):
    """
    Возвращает бинарный ответ сервера
    """

    response = HttpResponse(data)
    content_type = f'application/{conten_type}'
    content_disposition = f'attachment; filename="{report_name}"'
    response['Content-Type'] = content_type
    response['Content-Disposition'] = content_disposition
    response['Content-Transfer-Encoding'] = 'binary'
    return response
