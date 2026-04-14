from django.db import models

from core.mixins import TimeStampMixin


class AnalyticsSnapshot(TimeStampMixin):
    date = models.DateField(unique=True, verbose_name='日期')
    total_contracts = models.IntegerField(default=0, verbose_name='合同总数')
    total_amount = models.DecimalField(max_digits=18, decimal_places=2, default=0, verbose_name='合同总金额')
    active_contracts = models.IntegerField(default=0, verbose_name='生效合同数')
    completed_contracts = models.IntegerField(default=0, verbose_name='已完成合同数')
    new_contracts = models.IntegerField(default=0, verbose_name='新增合同数')
    new_amount = models.DecimalField(max_digits=18, decimal_places=2, default=0, verbose_name='新增合同金额')
    region_data = models.JSONField(default=dict, blank=True, verbose_name='区域分布')
    product_data = models.JSONField(default=dict, blank=True, verbose_name='产品分布')

    class Meta:
        db_table = 'analytics_snapshot'
        verbose_name = '分析快照'
        verbose_name_plural = verbose_name
        ordering = ['-date']

    def __str__(self):
        return f'Snapshot {self.date}'
