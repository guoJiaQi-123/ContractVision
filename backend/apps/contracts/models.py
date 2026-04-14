from django.conf import settings
from django.db import models

from core.mixins import SoftDeleteMixin, TimeStampMixin


class Contract(SoftDeleteMixin, TimeStampMixin):

    class Status(models.TextChoices):
        DRAFT = 'draft', '草稿'
        ACTIVE = 'active', '生效'
        COMPLETED = 'completed', '已完成'
        TERMINATED = 'terminated', '已终止'
        VOIDED = 'voided', '已作废'

    class PaymentStatus(models.TextChoices):
        UNPAID = 'unpaid', '未付款'
        PARTIAL = 'partial', '部分付款'
        PAID = 'paid', '已付清'

    class DeliveryStatus(models.TextChoices):
        PENDING = 'pending', '待交付'
        IN_PROGRESS = 'in_progress', '交付中'
        DELIVERED = 'delivered', '已交付'

    class Currency(models.TextChoices):
        CNY = 'CNY', '人民币'
        USD = 'USD', '美元'
        EUR = 'EUR', '欧元'

    class ApprovalStatus(models.TextChoices):
        NOT_REQUIRED = 'not_required', '无需审批'
        PENDING = 'pending', '待审批'
        APPROVED = 'approved', '已审批'
        REJECTED = 'rejected', '已驳回'

    class RenewalStatus(models.TextChoices):
        NONE = 'none', '未设置'
        PENDING = 'pending', '待续签'
        RENEWED = 'renewed', '已续签'
        EXPIRED = 'expired', '已到期'
        NOT_RENEWED = 'not_renewed', '未续签'

    contract_no = models.CharField(max_length=50, unique=True, verbose_name='合同编号')
    title = models.CharField(max_length=200, verbose_name='合同标题')
    client_name = models.CharField(max_length=100, verbose_name='客户名称')
    client_contact = models.CharField(max_length=50, blank=True, default='', verbose_name='客户联系人')
    contract_type = models.CharField(max_length=50, blank=True, default='', verbose_name='合同类型')
    product_type = models.CharField(max_length=50, blank=True, default='', verbose_name='产品类型')
    amount = models.DecimalField(max_digits=15, decimal_places=2, verbose_name='合同金额')
    base_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name='本位币金额')
    currency = models.CharField(
        max_length=10,
        choices=Currency.choices,
        default=Currency.CNY,
        verbose_name='货币',
    )
    region = models.CharField(max_length=50, blank=True, default='', verbose_name='区域')
    sign_date = models.DateField(null=True, blank=True, verbose_name='签订日期')
    start_date = models.DateField(null=True, blank=True, verbose_name='开始日期')
    end_date = models.DateField(null=True, blank=True, verbose_name='结束日期')
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
        verbose_name='合同状态',
    )
    payment_status = models.CharField(
        max_length=20,
        choices=PaymentStatus.choices,
        default=PaymentStatus.UNPAID,
        verbose_name='付款状态',
    )
    delivery_status = models.CharField(
        max_length=20,
        choices=DeliveryStatus.choices,
        default=DeliveryStatus.PENDING,
        verbose_name='交付状态',
    )
    salesperson = models.CharField(max_length=50, blank=True, default='', verbose_name='销售人员')
    department = models.CharField(max_length=50, blank=True, default='', verbose_name='部门')
    description = models.TextField(blank=True, default='', verbose_name='描述')
    attachments = models.JSONField(default=list, blank=True, verbose_name='附件')
    approval_status = models.CharField(
        max_length=20,
        choices=ApprovalStatus.choices,
        default=ApprovalStatus.NOT_REQUIRED,
        verbose_name='审批状态',
    )
    renewal_status = models.CharField(
        max_length=20,
        choices=RenewalStatus.choices,
        default=RenewalStatus.NONE,
        verbose_name='续签状态',
    )
    renewal_reminder_days = models.PositiveIntegerField(default=30, verbose_name='续签提醒天数')
    renewal_contract_no = models.CharField(max_length=50, blank=True, default='', verbose_name='续签合同编号')
    quality_score = models.PositiveIntegerField(default=100, verbose_name='数据质量评分')
    quality_issues = models.JSONField(default=list, blank=True, verbose_name='数据质量问题')
    stamp_tax_rate = models.DecimalField(max_digits=8, decimal_places=6, default=0, verbose_name='印花税税率')
    stamp_tax_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name='印花税金额')
    terminated_reason = models.TextField(blank=True, default='', verbose_name='终止/作废原因')
    terminated_at = models.DateField(null=True, blank=True, verbose_name='终止/作废时间')
    termination_attachments = models.JSONField(default=list, blank=True, verbose_name='终止凭证')
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='contracts',
        verbose_name='创建人',
    )
    renewal_owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='renewal_contracts',
        verbose_name='续签负责人',
    )

    class Meta:
        db_table = 'biz_contract'
        verbose_name = '合同'
        verbose_name_plural = verbose_name
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.contract_no} - {self.title}'


class ContractChangeLog(TimeStampMixin):
    contract = models.ForeignKey(
        Contract,
        on_delete=models.CASCADE,
        related_name='change_logs',
        verbose_name='合同',
    )
    field_name = models.CharField(max_length=50, verbose_name='变更字段')
    old_value = models.TextField(blank=True, default='', verbose_name='原值')
    new_value = models.TextField(blank=True, default='', verbose_name='新值')
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='变更人',
    )

    class Meta:
        db_table = 'biz_contract_change_log'
        verbose_name = '合同变更记录'
        verbose_name_plural = verbose_name
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.contract.contract_no} - {self.field_name}'


class PaymentPlan(TimeStampMixin):

    class Status(models.TextChoices):
        PENDING = 'pending', '待付款'
        PAID = 'paid', '已付款'
        OVERDUE = 'overdue', '逾期'
        SEVERE_OVERDUE = 'severe_overdue', '严重逾期'

    class InvoiceStatus(models.TextChoices):
        PENDING = 'pending', '待开票'
        ISSUED = 'issued', '已开票'
        RECEIVED = 'received', '已收票'

    contract = models.ForeignKey(
        Contract,
        on_delete=models.CASCADE,
        related_name='payment_plans',
        verbose_name='合同',
    )
    phase = models.CharField(max_length=50, verbose_name='付款阶段')
    ratio = models.DecimalField(max_digits=5, decimal_places=2, default=0, verbose_name='付款比例(%)')
    amount = models.DecimalField(max_digits=15, decimal_places=2, verbose_name='付款金额')
    actual_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name='实付金额')
    due_date = models.DateField(verbose_name='应付日期')
    paid_date = models.DateField(null=True, blank=True, verbose_name='实付日期')
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        verbose_name='状态',
    )
    invoice_status = models.CharField(
        max_length=20,
        choices=InvoiceStatus.choices,
        default=InvoiceStatus.PENDING,
        verbose_name='发票状态',
    )
    voucher_no = models.CharField(max_length=100, blank=True, default='', verbose_name='付款凭证号')
    remark = models.TextField(blank=True, default='', verbose_name='备注')

    class Meta:
        db_table = 'biz_payment_plan'
        verbose_name = '付款计划'
        verbose_name_plural = verbose_name
        ordering = ['due_date']

    def __str__(self):
        return f'{self.contract.contract_no} - {self.phase}'


class ContractMilestone(TimeStampMixin):

    class NodeType(models.TextChoices):
        DELIVERY = 'delivery', '交付节点'
        PAYMENT = 'payment', '付款节点'
        ACCEPTANCE = 'acceptance', '验收节点'
        CUSTOM = 'custom', '自定义节点'

    class Status(models.TextChoices):
        NOT_STARTED = 'not_started', '未开始'
        IN_PROGRESS = 'in_progress', '进行中'
        COMPLETED = 'completed', '已完成'
        OVERDUE = 'overdue', '已逾期'

    contract = models.ForeignKey(
        Contract,
        on_delete=models.CASCADE,
        related_name='milestones',
        verbose_name='合同',
    )
    node_type = models.CharField(max_length=20, choices=NodeType.choices, verbose_name='节点类型')
    name = models.CharField(max_length=100, verbose_name='节点名称')
    progress_weight = models.PositiveIntegerField(default=25, verbose_name='节点权重')
    planned_date = models.DateField(verbose_name='计划完成时间')
    actual_date = models.DateField(null=True, blank=True, verbose_name='实际完成时间')
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.NOT_STARTED,
        verbose_name='节点状态',
    )
    remark = models.TextField(blank=True, default='', verbose_name='备注')
    evidences = models.JSONField(default=list, blank=True, verbose_name='凭证')

    class Meta:
        db_table = 'biz_contract_milestone'
        verbose_name = '合同履约节点'
        verbose_name_plural = verbose_name
        ordering = ['planned_date', 'id']

    def __str__(self):
        return f'{self.contract.contract_no} - {self.name}'


class ContractChangeRequest(TimeStampMixin):

    class Status(models.TextChoices):
        PENDING = 'pending', '待审批'
        APPROVED = 'approved', '已审批'
        REJECTED = 'rejected', '已驳回'

    class ChangeType(models.TextChoices):
        CORE = 'core', '核心信息变更'
        SUPPLEMENT = 'supplement', '补充协议'

    contract = models.ForeignKey(
        Contract,
        on_delete=models.CASCADE,
        related_name='change_requests',
        verbose_name='合同',
    )
    change_type = models.CharField(max_length=20, choices=ChangeType.choices, default=ChangeType.CORE, verbose_name='变更类型')
    title = models.CharField(max_length=200, verbose_name='变更标题')
    reason = models.TextField(blank=True, default='', verbose_name='变更原因')
    effective_date = models.DateField(null=True, blank=True, verbose_name='生效日期')
    before_snapshot = models.JSONField(default=dict, blank=True, verbose_name='变更前快照')
    after_snapshot = models.JSONField(default=dict, blank=True, verbose_name='变更后快照')
    attachments = models.JSONField(default=list, blank=True, verbose_name='补充协议附件')
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING, verbose_name='审批状态')
    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='contract_change_requests',
        verbose_name='申请人',
    )
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_contract_change_requests',
        verbose_name='审批人',
    )
    approved_at = models.DateTimeField(null=True, blank=True, verbose_name='审批时间')

    class Meta:
        db_table = 'biz_contract_change_request'
        verbose_name = '合同变更申请'
        verbose_name_plural = verbose_name
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.contract.contract_no} - {self.title}'


class ApprovalProcess(TimeStampMixin):

    class ActionType(models.TextChoices):
        CREATE = 'create', '新增审批'
        UPDATE = 'update', '修改审批'
        DELETE = 'delete', '删除审批'
        CHANGE = 'change', '变更审批'

    name = models.CharField(max_length=100, verbose_name='流程名称')
    action_type = models.CharField(max_length=20, choices=ActionType.choices, verbose_name='操作类型')
    min_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name='触发金额下限')
    steps = models.JSONField(default=list, blank=True, verbose_name='审批步骤')
    is_active = models.BooleanField(default=True, verbose_name='是否启用')
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approval_processes',
        verbose_name='创建人',
    )

    class Meta:
        db_table = 'biz_approval_process'
        verbose_name = '审批流程'
        verbose_name_plural = verbose_name
        ordering = ['-updated_at']

    def __str__(self):
        return self.name


class ApprovalRequest(TimeStampMixin):

    class Status(models.TextChoices):
        PENDING = 'pending', '待审批'
        APPROVED = 'approved', '已通过'
        REJECTED = 'rejected', '已驳回'

    contract = models.ForeignKey(
        Contract,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='approval_requests',
        verbose_name='合同',
    )
    process = models.ForeignKey(
        ApprovalProcess,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='requests',
        verbose_name='审批流程',
    )
    action_type = models.CharField(max_length=20, choices=ApprovalProcess.ActionType.choices, verbose_name='操作类型')
    title = models.CharField(max_length=200, verbose_name='审批标题')
    request_payload = models.JSONField(default=dict, blank=True, verbose_name='审批数据')
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING, verbose_name='审批状态')
    current_step = models.PositiveIntegerField(default=1, verbose_name='当前步骤')
    review_logs = models.JSONField(default=list, blank=True, verbose_name='审批记录')
    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approval_requests',
        verbose_name='申请人',
    )
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_approval_requests',
        verbose_name='最后审批人',
    )
    reviewed_at = models.DateTimeField(null=True, blank=True, verbose_name='最后审批时间')

    class Meta:
        db_table = 'biz_approval_request'
        verbose_name = '审批申请'
        verbose_name_plural = verbose_name
        ordering = ['-created_at']

    def __str__(self):
        return self.title
