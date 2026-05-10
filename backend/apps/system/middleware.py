import json
import logging
import time

from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger(__name__)

ACTION_MAP = {
    'POST': 'CREATE',
    'PUT': 'UPDATE',
    'PATCH': 'UPDATE',
    'DELETE': 'DELETE',
}

EXCLUDE_PATHS = [
    '/admin/',
    '/api/v1/auth/token/refresh/',
    '/static/',
    '/media/',
]

SENSITIVE_GET_PATHS = [
    '/api/v1/system/logs/',
    '/api/v1/system/backup/',
    '/api/v1/system/integrations/',
    '/api/v1/system/data-permissions/',
    '/api/v1/system/alert-rules/',
    '/api/v1/contracts/',
]

MODULE_MAP = [
    ('/api/v1/contracts/', 'contracts'),
    ('/api/v1/users/', 'users'),
    ('/api/v1/auth/', 'auth'),
    ('/api/v1/system/logs/', 'system'),
    ('/api/v1/system/backup/', 'system'),
    ('/api/v1/system/integrations/', 'system'),
    ('/api/v1/system/data-permissions/', 'system'),
    ('/api/v1/system/alert-rules/', 'system'),
    ('/api/v1/system/alerts/', 'system'),
    ('/api/v1/system/alert-workspace/', 'system'),
    ('/api/v1/system/alert-center/', 'system'),
    ('/api/v1/system/sales-targets/', 'system'),
    ('/api/v1/system/dashboards/', 'system'),
    ('/api/v1/system/templates/', 'system'),
    ('/api/v1/system/currency-rates/', 'system'),
    ('/api/v1/system/stamp-tax-rules/', 'system'),
    ('/api/v1/system/mobile-dashboard/', 'system'),
]


def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


def resolve_module(path):
    for prefix, module_name in MODULE_MAP:
        if path.startswith(prefix):
            return module_name
    return ''


def resolve_level(status_code):
    if not status_code:
        return OperationLog.Level.INFO
    if status_code >= 500:
        return OperationLog.Level.ERROR
    if status_code >= 400:
        return OperationLog.Level.WARNING
    return OperationLog.Level.INFO


def resolve_category(action, status_code, path):
    if status_code and status_code >= 500:
        return OperationLog.Category.ERROR
    if path.startswith('/api/v1/auth/'):
        return OperationLog.Category.SECURITY
    if action in ('LOGIN', 'LOGOUT', 'LOGIN_FAILED'):
        return OperationLog.Category.SECURITY
    if action in ('ALERT_SCAN', 'ALERT_PROCESS', 'ALERT_REASSIGN'):
        return OperationLog.Category.SYSTEM
    if path.startswith('/api/v1/contracts/'):
        return OperationLog.Category.CONTRACT
    return OperationLog.Category.OPERATION


from .models import OperationLog


class OperationLogMiddleware(MiddlewareMixin):

    def process_request(self, request):
        request._log_start_time = time.time()

    def process_response(self, request, response):
        try:
            path = request.path

            for exclude_path in EXCLUDE_PATHS:
                if path.startswith(exclude_path):
                    return response

            if not hasattr(request, 'user') or not request.user.is_authenticated:
                return response

            method = request.method
            status_code = response.status_code

            if method == 'GET':
                is_sensitive = any(path.startswith(p) for p in SENSITIVE_GET_PATHS)
                if not is_sensitive:
                    return response
                action = 'VIEW'
            else:
                action = ACTION_MAP.get(method, method)

            if path.startswith('/api/v1/auth/login/'):
                if status_code >= 400:
                    action = 'LOGIN_FAILED'
                    category = OperationLog.Category.SECURITY
                    level = OperationLog.Level.WARNING
                else:
                    action = 'LOGIN'
                    category = OperationLog.Category.SECURITY
                    level = OperationLog.Level.INFO
            elif path.startswith('/api/v1/auth/logout/'):
                action = 'LOGOUT'
                category = OperationLog.Category.SECURITY
                level = OperationLog.Level.INFO
            else:
                category = resolve_category(action, status_code, path)
                level = resolve_level(status_code)

            if status_code and status_code >= 500:
                level = OperationLog.Level.ERROR
                category = OperationLog.Category.ERROR

            body_data = {}
            if method in ('POST', 'PUT', 'PATCH') and request.body:
                try:
                    parsed = json.loads(request.body.decode('utf-8'))
                    sensitive_keys = {'password', 'token', 'secret', 'auth_config', 'old_password', 'new_password'}
                    body_data = {k: '***' for k, v in parsed.items() if k in sensitive_keys} if isinstance(parsed, dict) else {}
                    if isinstance(parsed, dict):
                        for k, v in parsed.items():
                            if k not in sensitive_keys:
                                body_data[k] = v
                except Exception:
                    body_data = {'raw': request.body.decode('utf-8', errors='ignore')[:500]}

            duration_ms = None
            start_time = getattr(request, '_log_start_time', None)
            if start_time:
                duration_ms = int((time.time() - start_time) * 1000)

            user_agent = request.META.get('HTTP_USER_AGENT', '')[:500]

            detail = f'{method} {path}'
            if action == 'LOGIN':
                detail = '用户登录系统'
            elif action == 'LOGIN_FAILED':
                detail = '用户登录失败'
            elif action == 'LOGOUT':
                detail = '用户退出系统'
            elif action == 'VIEW':
                if path.startswith('/api/v1/contracts/'):
                    detail = '查看合同数据'
                else:
                    detail = f'查看 {path}'

            OperationLog.objects.create(
                user=request.user,
                ip_address=get_client_ip(request),
                action=action,
                target=path,
                detail=detail,
                after_data=body_data if method in ('POST', 'PUT', 'PATCH') else {},
                method=method,
                path=path,
                status_code=status_code,
                category=category,
                level=level,
                duration_ms=duration_ms,
                user_agent=user_agent,
                module=resolve_module(path),
            )
        except Exception as e:
            logger.error(f'Failed to log operation: {e}')

        return response
