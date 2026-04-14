import os
import subprocess
from datetime import datetime

from django.conf import settings
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from apps.users.permissions import IsAdmin
from core.response import error_response, success_response


BACKUP_DIR = os.path.join(settings.BASE_DIR, 'backups')


class BackupListView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    def get(self, request):
        if not os.path.exists(BACKUP_DIR):
            os.makedirs(BACKUP_DIR, exist_ok=True)

        backups = []
        for f in sorted(os.listdir(BACKUP_DIR), reverse=True):
            if f.endswith('.sql'):
                filepath = os.path.join(BACKUP_DIR, f)
                stat = os.stat(filepath)
                backups.append({
                    'filename': f,
                    'size': stat.st_size,
                    'created_at': datetime.fromtimestamp(stat.st_ctime).strftime('%Y-%m-%d %H:%M:%S'),
                })
        return success_response(data=backups)


class BackupCreateView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    def post(self, request):
        if not os.path.exists(BACKUP_DIR):
            os.makedirs(BACKUP_DIR, exist_ok=True)

        db = settings.DATABASES['default']
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'backup_{timestamp}.sql'
        filepath = os.path.join(BACKUP_DIR, filename)

        try:
            cmd = [
                'mysqldump',
                '-h', db['HOST'],
                '-P', str(db['PORT']),
                '-u', db['USER'],
                f'--password={db["PASSWORD"]}',
                db['NAME'],
            ]
            with open(filepath, 'w') as f:
                result = subprocess.run(cmd, stdout=f, stderr=subprocess.PIPE, timeout=300)

            if result.returncode != 0:
                return error_response(message=f'备份失败: {result.stderr.decode()}')

            stat = os.stat(filepath)
            return success_response(
                data={
                    'filename': filename,
                    'size': stat.st_size,
                    'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                },
                message='数据备份成功',
            )
        except FileNotFoundError:
            return error_response(message='mysqldump 命令未找到，请确认已安装 MySQL 客户端工具')
        except subprocess.TimeoutExpired:
            return error_response(message='备份超时')
        except Exception as e:
            return error_response(message=f'备份失败: {str(e)}')


class BackupRestoreView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    def post(self, request):
        filename = request.data.get('filename')
        if not filename:
            return error_response(message='请指定备份文件')

        filepath = os.path.join(BACKUP_DIR, filename)
        if not os.path.exists(filepath):
            return error_response(message='备份文件不存在')

        db = settings.DATABASES['default']
        try:
            cmd = [
                'mysql',
                '-h', db['HOST'],
                '-P', str(db['PORT']),
                '-u', db['USER'],
                f'--password={db["PASSWORD"]}',
                db['NAME'],
            ]
            with open(filepath, 'r') as f:
                result = subprocess.run(cmd, stdin=f, stderr=subprocess.PIPE, timeout=300)

            if result.returncode != 0:
                return error_response(message=f'恢复失败: {result.stderr.decode()}')

            return success_response(message='数据恢复成功')
        except Exception as e:
            return error_response(message=f'恢复失败: {str(e)}')


class BackupDeleteView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    def post(self, request):
        filename = request.data.get('filename')
        if not filename:
            return error_response(message='请指定备份文件')

        filepath = os.path.join(BACKUP_DIR, filename)
        if not os.path.exists(filepath):
            return error_response(message='备份文件不存在')

        os.remove(filepath)
        return success_response(message='备份文件已删除')
