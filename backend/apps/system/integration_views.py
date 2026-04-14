import requests
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated

from apps.users.permissions import IsAdmin
from core.response import error_response, success_response

from .models import IntegrationConfig
from .serializers import IntegrationConfigSerializer


class IntegrationConfigViewSet(viewsets.ModelViewSet):
    queryset = IntegrationConfig.objects.all()
    serializer_class = IntegrationConfigSerializer
    permission_classes = [IsAuthenticated, IsAdmin]
    ordering = ['-created_at']

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return success_response(data=serializer.data, message='接口配置创建成功')

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return success_response(data=serializer.data, message='接口配置更新成功')

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()
        return success_response(message='接口配置已删除')

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return success_response(data=serializer.data)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return success_response(data=serializer.data)

    @action(detail=True, methods=['post'])
    def test_connection(self, request, pk=None):
        config = self.get_object()
        try:
            headers = {}
            if config.auth_type == 'bearer' and config.auth_config.get('token'):
                headers['Authorization'] = f'Bearer {config.auth_config["token"]}'
            elif config.auth_type == 'api_key' and config.auth_config.get('api_key'):
                headers['X-API-Key'] = config.auth_config['api_key']

            response = requests.get(config.api_url, headers=headers, timeout=10)
            return success_response(
                data={
                    'status_code': response.status_code,
                    'success': response.status_code < 400,
                },
                message='连接测试成功' if response.status_code < 400 else f'连接失败，状态码: {response.status_code}',
            )
        except requests.exceptions.Timeout:
            return error_response(message='连接超时')
        except requests.exceptions.ConnectionError:
            return error_response(message='无法连接到目标服务器')
        except Exception as e:
            return error_response(message=f'连接测试失败: {str(e)}')

    @action(detail=True, methods=['post'])
    def toggle_status(self, request, pk=None):
        config = self.get_object()
        if config.status == 'active':
            config.status = 'inactive'
        else:
            config.status = 'active'
        config.save(update_fields=['status'])
        status_text = '启用' if config.status == 'active' else '停用'
        return success_response(message=f'接口已{status_text}')
