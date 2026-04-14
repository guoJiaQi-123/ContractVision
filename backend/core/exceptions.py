from rest_framework import status
from rest_framework.exceptions import (
    AuthenticationFailed,
    NotAuthenticated,
    PermissionDenied,
    ValidationError,
)
from rest_framework.views import exception_handler


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)

    if response is not None:
        if isinstance(exc, (NotAuthenticated, AuthenticationFailed)):
            response.data = {
                'code': 401,
                'message': '认证失败，请重新登录',
                'data': None,
            }
            response.status_code = status.HTTP_401_UNAUTHORIZED
        elif isinstance(exc, PermissionDenied):
            response.data = {
                'code': 403,
                'message': '没有操作权限',
                'data': None,
            }
            response.status_code = status.HTTP_403_FORBIDDEN
        elif isinstance(exc, ValidationError):
            if isinstance(exc.detail, dict):
                errors = {k: v[0] if isinstance(v, list) else v for k, v in exc.detail.items()}
            elif isinstance(exc.detail, list):
                errors = exc.detail
            else:
                errors = exc.detail
            response.data = {
                'code': 400,
                'message': '参数校验失败',
                'data': errors,
            }
            response.status_code = status.HTTP_400_BAD_REQUEST
        else:
            code_map = {
                status.HTTP_404_NOT_FOUND: (404, '资源不存在'),
                status.HTTP_405_METHOD_NOT_ALLOWED: (405, '请求方法不允许'),
                status.HTTP_429_TOO_MANY_REQUESTS: (429, '请求过于频繁'),
            }
            http_status = response.status_code
            if http_status in code_map:
                code, message = code_map[http_status]
                response.data = {
                    'code': code,
                    'message': message,
                    'data': None,
                }
            else:
                response.data = {
                    'code': response.status_code,
                    'message': str(exc.detail) if hasattr(exc, 'detail') else '请求错误',
                    'data': None,
                }

    return response
