from rest_framework.response import Response
from rest_framework import status


def custom_response(data, message, status_code, status_text=None, tokens=None, status_body="success"):
    status_code = int(status_code)

    response_data = {
        "status_code": status_code,
        "status_body": status_body,
        "message": message,
        "data": data,
    }

    if status_text is not None:
        response_data["status"] = status_text

    if tokens is not None:
        response_data["tokens"] = tokens

    return Response(response_data, status=status_code)
