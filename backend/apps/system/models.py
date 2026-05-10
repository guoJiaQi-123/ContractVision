from django.conf import settings
from django.db import models

from core.mixins import TimeStampMixin


class OperationLog(models.Model):
    class Category(models.TextChoices):
        OPERATION = 'operation', '操作日志'
        ERROR = 'error', '错误日志'
        SYSTEM = 'system', '系统日志'
        SECURITY = 'security', '安全日志'
        CONTRACT = 'contract', '合同日志'

    class Level(models.TextChoices):
        DEBUG = 'debug', 'DEBUG'
        INFO = 'info', 'INFO'
        WARNING = 'warning', 'WARNING'
        ERROR = 'error', 'ERROR'
        CRITICAL = 'critical', 'CRITICAL'

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='operation_logs',
        verbose_name='操作用户',
    )
    ip_address = models.GenericIPAddressField(null=True, blank=True, verbose_name='IP地址')
    action = models.CharField(max_length=50, verbose_name='操作类型')
    target = models.CharField(max_length=200, blank=True, default='', verbose_name='操作对象')
    detail = models.TextField(blank=True, default='', verbose_name='操作详情')
    before_data = models.JSONField(default=dict, blank=True, verbose_name='操作前数据')
    after_data = models.JSONField(default=dict, blank=True, verbose_name='操作后数据')
    method = models.CharField(max_length=10, blank=True, default='', verbose_name='请求方法')
    path = models.CharField(max_length=500, blank=True, default='', verbose_name='请求路径')
    status_code = models.IntegerField(null=True, blank=True, verbose_name='响应状态码')
    category = models.CharField(
        max_length=20,
        choices=Category.choices,
        default=Category.OPERATION,
        verbose_name='日志分类',
    )
    level = models.CharField(
        max_length=20,
        choices=Level.choices,
        default=Level.INFO,
        verbose_name='日志级别',
    )
    duration_ms = models.IntegerField(null=True, blank=True, verbose_name='耗时(ms)')
    user_agent = models.CharField(max_length=500, blank=True, default='', verbose_name='User-Agent')
    module = models.CharField(max_length=50, blank=True, default='', verbose_name='功能模块')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')

    class Meta:
        db_table = 'sys_operation_log'
        verbose_name = '操作日志'
        verbose_name_plural = verbose_name
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at'], name='idx_oplog_created'),
            models.Index(fields=['category', '-created_at'], name='idx_oplog_cat'),
            models.Index(fields=['level', '-created_at'], name='idx_oplog_level'),
            models.Index(fields=['action', '-created_at'], name='idx_oplog_action'),
            models.Index(fields=['user', '-created_at'], name='idx_oplog_user'),
        ]

    def __str__(self):
        return f'{self.user} - {self.action} - {self.target}'


class IntegrationConfig(models.Model):
    class Status(models.TextChoices):
        ACTIVE = 'active', '启用'
        INACTIVE = 'inactive', '停用'

    name = models.CharField(max_length=100, verbose_name='系统名称')
    system_type = models.CharField(max_length=50, verbose_name='系统类型')
    api_url = models.URLField(max_length=500, verbose_name='接口地址')
    auth_type = models.CharField(max_length=50, default='bearer', verbose_name='认证方式')
    auth_config = models.JSONField(default=dict, blank=True, verbose_name='认证配置')
    field_mapping = models.JSONField(default=dict, blank=True, verbose_name='字段映射')
    sync_interval = models.IntegerField(default=60, verbose_name='同步间隔(分钟)')
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.INACTIVE,
        verbose_name='状态',
    )
    last_sync_at = models.DateTimeField(null=True, blank=True, verbose_name='最后同步时间')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        db_table = 'sys_integration_config'
        verbose_name = '第三方集成配置'
        verbose_name_plural = verbose_name
        ordering = ['-created_at']

    def __str__(self):
        return self.name


class DataPermissionRule(models.Model):
    class ScopeType(models.TextChoices):
        ALL = 'all', '全部数据'
        SELF = 'self', '本人数据'
        DEPARTMENT = 'department', '部门数据'
        REGION = 'region', '区域数据'
        CUSTOMER = 'customer', '客户数据'

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='data_permission_rules',
        verbose_name='用户',
    )
    scope_type = models.CharField(max_length=20, choices=ScopeType.choices, default=ScopeType.SELF, verbose_name='权限范围')
    scope_value = models.CharField(max_length=100, blank=True, default='', verbose_name='范围值')
    can_edit = models.BooleanField(default=False, verbose_name='是否可编辑')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        db_table = 'sys_data_permission_rule'
        verbose_name = '数据权限规则'
        verbose_name_plural = verbose_name
        ordering = ['-updated_at']

    def __str__(self):
        return f'{self.user} - {self.scope_type}'


class AlertRule(models.Model):
    class RuleType(models.TextChoices):
        PAYMENT = 'payment_due', '付款到期'
        DELIVERY = 'delivery_due', '交付到期'
        CONTRACT = 'contract_expiry', '合同到期'
        INVOICE = 'invoice_due', '发票开具'
        TARGET = 'target_progress', '目标达成'

    name = models.CharField(max_length=100, verbose_name='规则名称')
    rule_type = models.CharField(max_length=30, choices=RuleType.choices, verbose_name='规则类型')
    remind_days = models.PositiveIntegerField(default=7, verbose_name='提前提醒天数')
    owner_role = models.CharField(max_length=20, blank=True, default='', verbose_name='推送角色')
    level = models.CharField(max_length=20, blank=True, default='medium', verbose_name='预警等级')
    is_active = models.BooleanField(default=True, verbose_name='是否启用')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        db_table = 'sys_alert_rule'
        verbose_name = '预警规则'
        verbose_name_plural = verbose_name
        ordering = ['-updated_at']

    def __str__(self):
        return self.name


class AlertMessage(models.Model):
    class Status(models.TextChoices):
        PENDING = 'pending', '待处理'
        PROCESSED = 'processed', '已处理'

    contract = models.ForeignKey(
        'contracts.Contract',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='alert_messages',
        verbose_name='合同',
    )
    rule = models.ForeignKey(
        AlertRule,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='messages',
        verbose_name='预警规则',
    )
    title = models.CharField(max_length=200, verbose_name='标题')
    content = models.TextField(blank=True, default='', verbose_name='内容')
    warning_type = models.CharField(max_length=30, verbose_name='预警类型')
    level = models.CharField(max_length=20, default='medium', verbose_name='预警等级')
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='alert_messages',
        verbose_name='负责人',
    )
    due_date = models.DateField(null=True, blank=True, verbose_name='截止时间')
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING, verbose_name='状态')
    processed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='processed_alert_messages',
        verbose_name='处理人',
    )
    processed_at = models.DateTimeField(null=True, blank=True, verbose_name='处理时间')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')

    class Meta:
        db_table = 'sys_alert_message'
        verbose_name = '预警消息'
        verbose_name_plural = verbose_name
        ordering = ['-created_at']

    def __str__(self):
        return self.title


class SalesTarget(models.Model):
    class TargetType(models.TextChoices):
        SALESPERSON = 'salesperson', '业务员'
        TEAM = 'team', '销售团队'
        DEPARTMENT = 'department', '销售部门'
        REGION = 'region', '区域'

    class PeriodType(models.TextChoices):
        YEAR = 'year', '年度'
        QUARTER = 'quarter', '季度'
        MONTH = 'month', '月度'

    name = models.CharField(max_length=100, verbose_name='目标名称')
    target_type = models.CharField(max_length=20, choices=TargetType.choices, verbose_name='目标维度')
    owner_value = models.CharField(max_length=100, verbose_name='目标对象')
    period_type = models.CharField(max_length=20, choices=PeriodType.choices, default=PeriodType.MONTH, verbose_name='周期类型')
    period_label = models.CharField(max_length=30, verbose_name='周期标识')
    start_date = models.DateField(verbose_name='开始日期')
    end_date = models.DateField(verbose_name='结束日期')
    target_amount = models.DecimalField(max_digits=15, decimal_places=2, verbose_name='目标金额')
    warning_threshold = models.DecimalField(max_digits=5, decimal_places=2, default=70, verbose_name='预警阈值(%)')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        db_table = 'sys_sales_target'
        verbose_name = '销售目标'
        verbose_name_plural = verbose_name
        ordering = ['-start_date', '-created_at']

    def __str__(self):
        return self.name


class DashboardConfig(models.Model):
    name = models.CharField(max_length=100, verbose_name='驾驶舱名称')
    role_scope = models.CharField(max_length=50, blank=True, default='', verbose_name='适用角色')
    layout = models.JSONField(default=list, blank=True, verbose_name='布局配置')
    widgets = models.JSONField(default=list, blank=True, verbose_name='组件配置')
    is_mobile = models.BooleanField(default=False, verbose_name='移动端模板')
    is_active = models.BooleanField(default=True, verbose_name='是否启用')
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='dashboard_configs',
        verbose_name='创建人',
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        db_table = 'sys_dashboard_config'
        verbose_name = '驾驶舱配置'
        verbose_name_plural = verbose_name
        ordering = ['-updated_at']

    def __str__(self):
        return self.name


class DataTemplate(models.Model):
    class TemplateType(models.TextChoices):
        IMPORT = 'import', '导入模板'
        EXPORT = 'export', '导出模板'
        REPORT = 'report', '报表模板'

    name = models.CharField(max_length=100, verbose_name='模板名称')
    template_type = models.CharField(max_length=20, choices=TemplateType.choices, verbose_name='模板类型')
    version = models.CharField(max_length=20, default='v1.0', verbose_name='版本号')
    field_config = models.JSONField(default=list, blank=True, verbose_name='字段配置')
    validation_rules = models.JSONField(default=list, blank=True, verbose_name='校验规则')
    is_active = models.BooleanField(default=True, verbose_name='是否启用')
    description = models.TextField(blank=True, default='', verbose_name='说明')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        db_table = 'sys_data_template'
        verbose_name = '数据模板'
        verbose_name_plural = verbose_name
        ordering = ['-updated_at']

    def __str__(self):
        return self.name


class CurrencyRate(models.Model):
    currency = models.CharField(max_length=10, verbose_name='币种')
    base_currency = models.CharField(max_length=10, default='CNY', verbose_name='本位币')
    rate = models.DecimalField(max_digits=15, decimal_places=6, verbose_name='汇率')
    effective_date = models.DateField(verbose_name='生效日期')
    is_latest = models.BooleanField(default=True, verbose_name='是否最新汇率')
    remark = models.CharField(max_length=200, blank=True, default='', verbose_name='备注')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        db_table = 'sys_currency_rate'
        verbose_name = '汇率配置'
        verbose_name_plural = verbose_name
        ordering = ['-effective_date', '-updated_at']

    def __str__(self):
        return f'{self.currency}/{self.base_currency} {self.rate}'


class StampTaxRule(models.Model):
    contract_type = models.CharField(max_length=50, verbose_name='合同类型')
    rate = models.DecimalField(max_digits=8, decimal_places=6, verbose_name='税率')
    description = models.CharField(max_length=200, blank=True, default='', verbose_name='说明')
    is_active = models.BooleanField(default=True, verbose_name='是否启用')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        db_table = 'sys_stamp_tax_rule'
        verbose_name = '印花税规则'
        verbose_name_plural = verbose_name
        ordering = ['-updated_at']

    def __str__(self):
        return self.contract_type


class Department(TimeStampMixin):
    name = models.CharField(max_length=100, verbose_name='部门名称')
    code = models.CharField(max_length=50, unique=True, verbose_name='部门编码')
    parent = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='children', verbose_name='上级部门')
    manager = models.CharField(max_length=50, blank=True, default='', verbose_name='部门负责人')
    description = models.TextField(blank=True, default='', verbose_name='描述')
    is_active = models.BooleanField(default=True, verbose_name='是否启用')
    sort_order = models.PositiveIntegerField(default=0, verbose_name='排序')

    class Meta:
        db_table = 'biz_department'
        verbose_name = '部门'
        verbose_name_plural = verbose_name
        ordering = ['sort_order', 'id']

    def __str__(self):
        return self.name


class ProductType(TimeStampMixin):
    name = models.CharField(max_length=100, verbose_name='产品类型名称')
    code = models.CharField(max_length=50, unique=True, verbose_name='产品类型编码')
    category = models.CharField(max_length=50, blank=True, default='', verbose_name='产品分类')
    description = models.TextField(blank=True, default='', verbose_name='描述')
    is_active = models.BooleanField(default=True, verbose_name='是否启用')
    sort_order = models.PositiveIntegerField(default=0, verbose_name='排序')

    class Meta:
        db_table = 'biz_product_type'
        verbose_name = '产品类型'
        verbose_name_plural = verbose_name
        ordering = ['sort_order', 'id']

    def __str__(self):
        return self.name


class Customer(TimeStampMixin):
    class CustomerLevel(models.TextChoices):
        VIP = 'vip', 'VIP客户'
        NORMAL = 'normal', '普通客户'
        POTENTIAL = 'potential', '潜在客户'

    name = models.CharField(max_length=200, verbose_name='客户名称')
    code = models.CharField(max_length=50, unique=True, verbose_name='客户编码')
    short_name = models.CharField(max_length=100, blank=True, default='', verbose_name='客户简称')
    level = models.CharField(max_length=20, choices=CustomerLevel.choices, default=CustomerLevel.NORMAL, verbose_name='客户等级')
    contact_person = models.CharField(max_length=50, blank=True, default='', verbose_name='联系人')
    contact_phone = models.CharField(max_length=20, blank=True, default='', verbose_name='联系电话')
    contact_email = models.CharField(max_length=100, blank=True, default='', verbose_name='联系邮箱')
    address = models.CharField(max_length=300, blank=True, default='', verbose_name='地址')
    region = models.CharField(max_length=50, blank=True, default='', verbose_name='区域')
    industry = models.CharField(max_length=50, blank=True, default='', verbose_name='行业')
    description = models.TextField(blank=True, default='', verbose_name='描述')
    is_active = models.BooleanField(default=True, verbose_name='是否启用')

    class Meta:
        db_table = 'biz_customer'
        verbose_name = '客户'
        verbose_name_plural = verbose_name
        ordering = ['-created_at']

    def __str__(self):
        return self.name
