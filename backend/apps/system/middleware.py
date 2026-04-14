import logging
import json

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
    '/api/v1/auth/login/',
    '/api/v1/auth/register/',
    '/api/v1/auth/token/refresh/',
    '/static/',
    '/media/',
]


def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


class OperationLogMiddleware(MiddlewareMixin):

    def process_response(self, request, response):
        try:
            if request.method == 'GET':
                return response

            path = request.path
            for exclude_path in EXCLUDE_PATHS:
                if path.startswith(exclude_path):
                    return response

            if not hasattr(request, 'user') or not request.user.is_authenticated:
                return response

            body_data = {}
            if request.body:
                try:
                    body_data = json.loads(request.body.decode('utf-8'))
                except Exception:
                    body_data = {'raw': request.body.decode('utf-8', errors='ignore')[:1000]}

            from .models import OperationLog
            OperationLog.objects.create(
                user=request.user,
                ip_address=get_client_ip(request),
                action=ACTION_MAP.get(request.method, request.method),
                target=path,
                detail=f'{request.method} {path}',
                after_data=body_data if request.method in ('POST', 'PUT', 'PATCH') else {},
                method=request.method,
                path=path,
                status_code=response.status_code,
            )
        except Exception as e:
            logger.error(f'Failed to log operation: {e}')

        return response
