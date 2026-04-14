from __future__ import annotations

from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from difflib import SequenceMatcher

from django.db.models import Q
from django.utils import timezone

from apps.system.models import CurrencyRate, DataPermissionRule, StampTaxRule

from .models import Contract, PaymentPlan


def quantize_amount(value) -> Decimal:
    return Decimal(value or 0).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)


def get_currency_rate(currency: str, target_date: date | None = None) -> Decimal:
    if not currency or currency == Contract.Currency.CNY:
        return Decimal('1')
    target_date = target_date or timezone.now().date()
    rate = (
        CurrencyRate.objects
        .filter(currency=currency, effective_date__lte=target_date)
        .order_by('-effective_date')
        .first()
    )
    return Decimal(rate.rate) if rate else Decimal('1')


def compute_base_amount(contract: Contract | dict) -> Decimal:
    amount = quantize_amount(getattr(contract, 'amount', None) if not isinstance(contract, dict) else contract.get('amount'))
    currency = getattr(contract, 'currency', None) if not isinstance(contract, dict) else contract.get('currency')
    sign_date = getattr(contract, 'sign_date', None) if not isinstance(contract, dict) else contract.get('sign_date')
    return quantize_amount(amount * get_currency_rate(currency or Contract.Currency.CNY, sign_date))


def compute_stamp_tax(contract: Contract | dict) -> tuple[Decimal, Decimal]:
    contract_type = getattr(contract, 'contract_type', None) if not isinstance(contract, dict) else contract.get('contract_type')
    if not contract_type and not isinstance(contract, dict):
        contract_type = contract.product_type
    if not contract_type and isinstance(contract, dict):
        contract_type = contract.get('product_type')

    rule = StampTaxRule.objects.filter(contract_type=contract_type, is_active=True).order_by('-updated_at').first()
    rate = Decimal(rule.rate) if rule else Decimal('0')
    base_amount = compute_base_amount(contract)
    tax_amount = quantize_amount(base_amount * rate)
    return rate, tax_amount


def payment_overdue_meta(plan: PaymentPlan) -> dict:
    today = timezone.now().date()
    due_date = plan.due_date
    if plan.paid_date:
        overdue_days = max((plan.paid_date - due_date).days, 0)
    else:
        overdue_days = max((today - due_date).days, 0)

    if overdue_days <= 0:
        level = 'normal'
    elif overdue_days <= 7:
        level = 'attention'
    elif overdue_days <= 30:
        level = 'overdue'
    else:
        level = 'severe'
    return {
        'overdue_days': overdue_days,
        'overdue_level': level,
    }


def compute_contract_progress(contract: Contract) -> dict:
    milestones = list(contract.milestones.all())
    total_weight = sum(item.progress_weight for item in milestones) or 0
    completed_weight = sum(item.progress_weight for item in milestones if item.status == item.Status.COMPLETED)
    risk_count = 0
    today = timezone.now().date()
    node_items = []

    for milestone in milestones:
        is_risk = bool(milestone.planned_date and milestone.planned_date < today and milestone.status != milestone.Status.COMPLETED)
        if is_risk:
            risk_count += 1
        node_items.append({
            'id': milestone.id,
            'node_type': milestone.node_type,
            'name': milestone.name,
            'status': milestone.status,
            'planned_date': milestone.planned_date,
            'actual_date': milestone.actual_date,
            'progress_weight': milestone.progress_weight,
            'remark': milestone.remark,
            'is_risk': is_risk,
        })

    completion_rate = round(completed_weight / total_weight * 100, 2) if total_weight else 0
    return {
        'completion_rate': completion_rate,
        'risk_count': risk_count,
        'milestone_count': len(node_items),
        'nodes': node_items,
    }


def compute_quality_issues(contract: Contract) -> list[dict]:
    issues = []
    required_fields = {
        'contract_no': contract.contract_no,
        'title': contract.title,
        'client_name': contract.client_name,
        'amount': contract.amount,
        'sign_date': contract.sign_date,
        'end_date': contract.end_date,
        'salesperson': contract.salesperson,
    }
    for field, value in required_fields.items():
        if value in (None, '', []):
            issues.append({
                'field': field,
                'severity': 'high',
                'reason': '关键字段缺失',
                'suggestion': '请补充完整后重新校验',
            })

    if contract.start_date and contract.end_date and contract.start_date > contract.end_date:
        issues.append({
            'field': 'date_range',
            'severity': 'high',
            'reason': '开始日期晚于结束日期',
            'suggestion': '请修正合同有效期范围',
        })
    if contract.amount is not None and Decimal(contract.amount) <= 0:
        issues.append({
            'field': 'amount',
            'severity': 'high',
            'reason': '合同金额必须大于 0',
            'suggestion': '请修正金额后重新校验',
        })
    if contract.currency != Contract.Currency.CNY and Decimal(contract.base_amount or 0) <= 0:
        issues.append({
            'field': 'base_amount',
            'severity': 'medium',
            'reason': '缺少有效汇率换算结果',
            'suggestion': '请维护汇率并重新计算本位币金额',
        })
    if not contract.payment_plans.exists():
        issues.append({
            'field': 'payment_plans',
            'severity': 'low',
            'reason': '未配置付款计划',
            'suggestion': '建议维护回款节点，便于逾期跟踪',
        })
    return issues


def compute_quality_score(contract: Contract) -> tuple[int, list[dict]]:
    issues = compute_quality_issues(contract)
    deduction_map = {'high': 20, 'medium': 10, 'low': 5}
    score = 100
    for issue in issues:
        score -= deduction_map.get(issue['severity'], 5)
    return max(score, 0), issues


def update_contract_metrics(contract: Contract, save: bool = True) -> Contract:
    contract.base_amount = compute_base_amount(contract)
    rate, tax_amount = compute_stamp_tax(contract)
    contract.stamp_tax_rate = rate
    contract.stamp_tax_amount = tax_amount
    score, issues = compute_quality_score(contract)
    contract.quality_score = score
    contract.quality_issues = issues
    if save:
        contract.save(update_fields=[
            'base_amount',
            'stamp_tax_rate',
            'stamp_tax_amount',
            'quality_score',
            'quality_issues',
            'updated_at',
        ])
    return contract


def apply_data_permission(queryset, user):
    if not user or not user.is_authenticated or user.role == 'admin':
        return queryset

    rules = list(user.data_permission_rules.all())
    if not rules:
        if user.role == 'viewer':
            return queryset.filter(Q(salesperson=user.username) | Q(created_by=user))
        return queryset

    condition = Q(pk__isnull=False)
    scoped = Q(pk__in=[])
    has_all = False
    for rule in rules:
        if rule.scope_type == DataPermissionRule.ScopeType.ALL:
            has_all = True
            break
        if rule.scope_type == DataPermissionRule.ScopeType.SELF:
            scoped |= Q(salesperson=user.username) | Q(created_by=user)
        elif rule.scope_type == DataPermissionRule.ScopeType.DEPARTMENT:
            scoped |= Q(department=rule.scope_value or user.department)
        elif rule.scope_type == DataPermissionRule.ScopeType.REGION:
            scoped |= Q(region=rule.scope_value or user.region)
        elif rule.scope_type == DataPermissionRule.ScopeType.CUSTOMER:
            scoped |= Q(client_name__icontains=rule.scope_value)
    if has_all:
        return queryset
    return queryset.filter(condition & scoped)


def find_duplicate_contracts(queryset) -> list[dict]:
    records = list(queryset.values('id', 'contract_no', 'client_name', 'title', 'amount', 'sign_date'))
    groups = []
    used = set()
    for index, current in enumerate(records):
        if current['id'] in used:
            continue
        group = [current]
        for candidate in records[index + 1:]:
            if candidate['id'] in used:
                continue
            contract_no_match = current['contract_no'] and candidate['contract_no'] and current['contract_no'] == candidate['contract_no']
            client_similarity = SequenceMatcher(None, current['client_name'] or '', candidate['client_name'] or '').ratio()
            title_similarity = SequenceMatcher(None, current['title'] or '', candidate['title'] or '').ratio()
            amount_gap = abs(Decimal(current['amount'] or 0) - Decimal(candidate['amount'] or 0))
            if contract_no_match or ((client_similarity > 0.8 or title_similarity > 0.8) and amount_gap <= Decimal('1')):
                similarity = 1.0 if contract_no_match else round(max(client_similarity, title_similarity), 2)
                item = dict(candidate)
                item['similarity'] = similarity
                group.append(item)
                used.add(candidate['id'])
        if len(group) > 1:
            group[0]['similarity'] = 1.0
            used.add(current['id'])
            groups.append({
                'primary_id': group[0]['id'],
                'contracts': group,
            })
    return groups
