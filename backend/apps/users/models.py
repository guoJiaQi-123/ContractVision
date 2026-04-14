from django.contrib.auth.models import AbstractUser
from django.db import models

from utils.validators import validate_phone


class User(AbstractUser):

    class Role(models.TextChoices):
        ADMIN = 'admin', '管理员'
        OPERATOR = 'operator', '操作员'
        VIEWER = 'viewer', '查看者'

    phone = models.CharField(
        max_length=11,
        blank=True,
        default='',
        validators=[validate_phone],
        verbose_name='手机号',
    )
    company_name = models.CharField(max_length=100, blank=True, default='', verbose_name='公司名称')
    department = models.CharField(max_length=50, blank=True, default='', verbose_name='部门')
    region = models.CharField(max_length=50, blank=True, default='', verbose_name='区域')
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.VIEWER,
        verbose_name='角色',
    )
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True, verbose_name='头像')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        db_table = 'sys_user'
        verbose_name = '用户'
        verbose_name_plural = verbose_name
        ordering = ['-created_at']

    def __str__(self):
        return self.username

    @property
    def is_admin(self):
        return self.role == self.Role.ADMIN

    @property
    def is_operator(self):
        return self.role == self.Role.OPERATOR

    @property
    def is_viewer(self):
        return self.role == self.Role.VIEWER
