from rest_framework.response import Response


class ApiResponse(Response):

    def __init__(self, data=None, code=200, message='success', status=None, **kwargs):
        response_data = {
            'code': code,
            'message': message,
            'data': data,
        }
        if status is None:
            if code == 200:
                status = 200
            elif code == 400:
                status = 400
            elif code == 401:
                status = 401
            elif code == 403:
                status = 403
            elif code == 500:
                status = 500
            else:
                status = 200
        super().__init__(data=response_data, status=status, **kwargs)


def success_response(data=None, message='success'):
    return ApiResponse(data=data, code=200, message=message)


def error_response(message='error', code=400, data=None):
    return ApiResponse(data=data, code=code, message=message)


def unauthorized_response(message='未授权'):
    return ApiResponse(code=401, message=message)


def forbidden_response(message='无权限'):
    return ApiResponse(code=403, message=message)


def server_error_response(message='服务器内部错误'):
    return ApiResponse(code=500, message=message)
