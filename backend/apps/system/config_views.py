import csv
from datetime import timedelta
from decimal import Decimal

from django.db.models import Q, Sum
from django.http import HttpResponse
from django.utils import timezone
from rest_framework import mixins
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from apps.contracts.models import Contract, ContractMilestone, PaymentPlan
from apps.users.models import User
from apps.users.permissions import IsAdmin, IsViewer
from core.response import error_response, success_response

from .models import (
    AlertMessage,
    AlertRule,
    CurrencyRate,
    DashboardConfig,
    DataPermissionRule,
    DataTemplate,
    OperationLog,
    SalesTarget,
    StampTaxRule,
)
from .serializers import (
    AlertMessageSerializer,
    AlertRuleSerializer,
    CurrencyRateSerializer,
    DashboardConfigSerializer,
    DataPermissionRuleSerializer,
    DataTemplateSerializer,
    SalesTargetSerializer,
    StampTaxRuleSerializer,
)


def get_business_users():
    return User.objects.filter(role__in=[User.Role.ADMIN, User.Role.OPERATOR]).order_by(
        "role", "id"
    )


def get_contract_owner_candidates(contract):
    queryset = get_business_users()
    if not contract:
        return queryset

    if contract.department:
        department_queryset = queryset.filter(department=contract.department)
        if department_queryset.exists():
            return department_queryset

    if contract.region:
        region_queryset = queryset.filter(region=contract.region)
        if region_queryset.exists():
            return region_queryset

    return queryset


def resolve_contract_alert_owner(contract, warning_type, owner_role=""):
    if not contract:
        return None

    strategy_value = normalize_owner_strategy(warning_type, owner_role)
    created_by = contract.created_by if is_business_user(contract.created_by) else None
    renewal_owner = (
        contract.renewal_owner if is_business_user(contract.renewal_owner) else None
    )

    if strategy_value == "creator" and created_by:
        return created_by
    if strategy_value == "renewal_owner" and renewal_owner:
        return renewal_owner
    if strategy_value == "department_operator":
        owner = get_department_operator(contract)
        if owner:
            return owner
    if strategy_value == "region_operator":
        owner = get_region_operator(contract)
        if owner:
            return owner
    if strategy_value == "admin_pool":
        owner = get_admin_user()
        if owner:
            return owner
    if strategy_value == "business_pool":
        owner = get_contract_owner_candidates(contract).first()
        if owner:
            return owner

    if warning_type == AlertRule.RuleType.CONTRACT and renewal_owner:
        return renewal_owner
    if warning_type in [AlertRule.RuleType.PAYMENT, AlertRule.RuleType.INVOICE]:
        if created_by:
            return created_by
    if warning_type == AlertRule.RuleType.DELIVERY:
        owner = get_department_operator(contract)
        if owner:
            return owner
    if renewal_owner:
        return renewal_owner
    if created_by:
        return created_by
    owner = get_contract_owner_candidates(contract).first()
    if owner:
        return owner
    return get_admin_user()


def resolve_target_alert_owner(target, related_contract_queryset, owner_role=""):
    business_users = get_business_users()
    strategy_value = normalize_owner_strategy(AlertRule.RuleType.TARGET, owner_role)

    if strategy_value == "admin_pool":
        return get_admin_user()

    if strategy_value == "business_pool":
        return business_users.first()

    matched_contract = related_contract_queryset.order_by("-created_at").first()
    if strategy_value == "latest_contract_owner" and matched_contract:
        return resolve_contract_alert_owner(
            matched_contract,
            AlertRule.RuleType.CONTRACT,
            owner_role="renewal_owner",
        )

    if target.target_type == SalesTarget.TargetType.DEPARTMENT:
        owner = business_users.filter(department=target.owner_value).first()
        if owner:
            return owner
    if target.target_type == SalesTarget.TargetType.REGION:
        owner = business_users.filter(region=target.owner_value).first()
        if owner:
            return owner
    if target.target_type == SalesTarget.TargetType.SALESPERSON and matched_contract:
        owner = resolve_contract_alert_owner(
            matched_contract,
            AlertRule.RuleType.CONTRACT,
            owner_role="renewal_owner",
        )
        if owner:
            return owner
    if target.target_type == SalesTarget.TargetType.TEAM:
        owner = business_users.filter(department__icontains=target.owner_value).first()
        if owner:
            return owner
    return business_users.first()


def get_warning_type_label(warning_type):
    label_map = {
        AlertRule.RuleType.PAYMENT: "付款到期",
        AlertRule.RuleType.DELIVERY: "交付到期",
        AlertRule.RuleType.CONTRACT: "合同到期",
        AlertRule.RuleType.INVOICE: "发票开具",
        AlertRule.RuleType.TARGET: "目标达成",
    }
    return label_map.get(warning_type, warning_type or "")


def get_default_owner_strategy_value(warning_type):
    default_map = {
        AlertRule.RuleType.PAYMENT: "creator",
        AlertRule.RuleType.DELIVERY: "department_operator",
        AlertRule.RuleType.CONTRACT: "renewal_owner",
        AlertRule.RuleType.INVOICE: "creator",
        AlertRule.RuleType.TARGET: "target_dimension",
    }
    return default_map.get(warning_type, "business_pool")


def get_owner_strategy_options(warning_type):
    strategy_map = {
        AlertRule.RuleType.PAYMENT: [
            {
                "value": "creator",
                "label": "合同创建人",
                "description": "优先归属合同创建人，适合付款审批与回款跟进。",
            },
            {
                "value": "renewal_owner",
                "label": "续签负责人",
                "description": "归属续签负责人，适合由客户经营 owner 统一接手账期推进。",
            },
            {
                "value": "department_operator",
                "label": "部门操作员",
                "description": "优先匹配同部门操作员，便于财务资料和执行动作协同。",
            },
            {
                "value": "business_pool",
                "label": "业务候选池",
                "description": "按合同部门/区域候选池自动兜底，适合跨人协同的场景。",
            },
            {
                "value": "admin_pool",
                "label": "管理员池",
                "description": "优先分配给管理员，适合需要集中统筹的风险事项。",
            },
        ],
        AlertRule.RuleType.DELIVERY: [
            {
                "value": "department_operator",
                "label": "部门操作员",
                "description": "优先匹配同部门操作员，适合交付执行和节点回传。",
            },
            {
                "value": "region_operator",
                "label": "区域操作员",
                "description": "优先匹配同区域操作员，适合区域交付组织协调。",
            },
            {
                "value": "creator",
                "label": "合同创建人",
                "description": "由原业务创建人跟进交付风险，减少交接成本。",
            },
            {
                "value": "renewal_owner",
                "label": "续签负责人",
                "description": "由客户经营 owner 统筹交付与续签风险闭环。",
            },
            {
                "value": "business_pool",
                "label": "业务候选池",
                "description": "从合同候选负责人池自动兜底分配。",
            },
        ],
        AlertRule.RuleType.CONTRACT: [
            {
                "value": "renewal_owner",
                "label": "续签负责人",
                "description": "优先归属续签负责人，适合到期谈判与续约推进。",
            },
            {
                "value": "creator",
                "label": "合同创建人",
                "description": "由原业务创建人承接到期风险，适合单 owner 客户关系场景。",
            },
            {
                "value": "department_operator",
                "label": "部门操作员",
                "description": "优先匹配部门操作员，适合续签资料和执行跟进协同。",
            },
            {
                "value": "business_pool",
                "label": "业务候选池",
                "description": "从合同部门/区域候选池自动兜底匹配。",
            },
            {
                "value": "admin_pool",
                "label": "管理员池",
                "description": "归属管理员统一统筹高风险到期合同。",
            },
        ],
        AlertRule.RuleType.INVOICE: [
            {
                "value": "creator",
                "label": "合同创建人",
                "description": "优先归属合同创建人，适合开票资料和客户沟通闭环。",
            },
            {
                "value": "renewal_owner",
                "label": "续签负责人",
                "description": "由客户经营 owner 统一推进开票与回款节奏。",
            },
            {
                "value": "department_operator",
                "label": "部门操作员",
                "description": "由执行侧操作员承接开票流转和资料准备。",
            },
            {
                "value": "business_pool",
                "label": "业务候选池",
                "description": "按合同候选负责人池自动兜底分配。",
            },
            {
                "value": "admin_pool",
                "label": "管理员池",
                "description": "由管理员统一处理需要跨部门协调的开票事项。",
            },
        ],
        AlertRule.RuleType.TARGET: [
            {
                "value": "target_dimension",
                "label": "目标维度负责人",
                "description": "按部门、区域、销售或团队维度自动匹配对应负责人。",
            },
            {
                "value": "latest_contract_owner",
                "label": "最近成交合同负责人",
                "description": "回落到该维度最近成交合同的负责人，适合沿用最新经营 owner。",
            },
            {
                "value": "business_pool",
                "label": "业务候选池",
                "description": "从业务候选池兜底匹配目标预警负责人。",
            },
            {
                "value": "admin_pool",
                "label": "管理员池",
                "description": "由管理层统一承接目标偏差预警。",
            },
        ],
    }
    return strategy_map.get(warning_type, [])


def normalize_owner_strategy(warning_type, owner_role):
    option_values = {item["value"] for item in get_owner_strategy_options(warning_type)}
    value = (owner_role or "").strip()
    if value in option_values:
        return value
    legacy_map = {
        "operator": get_default_owner_strategy_value(warning_type),
        "admin": "admin_pool",
    }
    return legacy_map.get(value) or get_default_owner_strategy_value(warning_type)


def get_owner_strategy_meta(warning_type, owner_role):
    strategy_value = normalize_owner_strategy(warning_type, owner_role)
    strategy_option = next(
        (
            item
            for item in get_owner_strategy_options(warning_type)
            if item["value"] == strategy_value
        ),
        None,
    ) or {
        "value": strategy_value,
        "label": strategy_value,
        "description": "系统自动匹配负责人。",
    }
    default_value = get_default_owner_strategy_value(warning_type)
    default_option = (
        next(
            (
                item
                for item in get_owner_strategy_options(warning_type)
                if item["value"] == default_value
            ),
            None,
        )
        or strategy_option
    )
    return {
        "value": strategy_option["value"],
        "label": strategy_option["label"],
        "description": strategy_option["description"],
        "is_default": strategy_option["value"] == default_value,
        "default_value": default_option["value"],
        "default_label": default_option["label"],
    }


def get_admin_user():
    return (
        User.objects.filter(role=User.Role.ADMIN).order_by("id").first()
        or get_business_users().first()
    )


def get_department_operator(contract):
    if not contract:
        return None
    operators = User.objects.filter(role=User.Role.OPERATOR).order_by("id")
    if contract.department:
        owner = operators.filter(department=contract.department).first()
        if owner:
            return owner
    if contract.region:
        owner = operators.filter(region=contract.region).first()
        if owner:
            return owner
    return None


def get_region_operator(contract):
    if not contract:
        return None
    operators = User.objects.filter(role=User.Role.OPERATOR).order_by("id")
    if contract.region:
        owner = operators.filter(region=contract.region).first()
        if owner:
            return owner
    if contract.department:
        owner = operators.filter(department=contract.department).first()
        if owner:
            return owner
    return None


def get_owner_strategy_catalog():
    rule_map = {
        rule.rule_type: rule
        for rule in AlertRule.objects.filter(is_active=True).order_by("id")
    }
    catalog = []
    for warning_type in [
        AlertRule.RuleType.PAYMENT,
        AlertRule.RuleType.DELIVERY,
        AlertRule.RuleType.CONTRACT,
        AlertRule.RuleType.INVOICE,
        AlertRule.RuleType.TARGET,
    ]:
        strategy_meta = get_owner_strategy_meta(
            warning_type, getattr(rule_map.get(warning_type), "owner_role", "")
        )
        catalog.append(
            {
                "warning_type": warning_type,
                "title": get_warning_type_label(warning_type),
                "description": strategy_meta["description"],
                "configured_label": strategy_meta["label"],
                "configured_value": strategy_meta["value"],
                "recommended_label": strategy_meta["default_label"],
                "recommended_value": strategy_meta["default_value"],
                "is_default": strategy_meta["is_default"],
                "rule_name": getattr(rule_map.get(warning_type), "name", ""),
                "options": get_owner_strategy_options(warning_type),
            }
        )
    return catalog


def is_business_user(user):
    return bool(user and user.role in [User.Role.ADMIN, User.Role.OPERATOR])


def describe_contract_owner_resolution(contract, warning_type, owner, owner_role=""):
    strategy_meta = get_owner_strategy_meta(warning_type, owner_role)
    if not contract:
        return {
            "strategy_title": strategy_meta["label"],
            "reason": f"当前规则配置为「{strategy_meta['label']}」，但本条预警未关联合同，无法按合同维度推断负责人。",
        }
    if owner:
        reason_map = {
            "creator": f"当前规则配置为「{strategy_meta['label']}」，已命中合同创建人 {owner.username}。",
            "renewal_owner": f"当前规则配置为「{strategy_meta['label']}」，已命中续签负责人 {owner.username}。",
            "department_operator": f"当前规则配置为「{strategy_meta['label']}」，已按合同部门/区域匹配操作员 {owner.username}。",
            "region_operator": f"当前规则配置为「{strategy_meta['label']}」，已按合同区域/部门匹配操作员 {owner.username}。",
            "business_pool": f"当前规则配置为「{strategy_meta['label']}」，已从业务候选池匹配负责人 {owner.username}。",
            "admin_pool": f"当前规则配置为「{strategy_meta['label']}」，已分配给管理员 {owner.username} 统筹处理。",
        }
        return {
            "strategy_title": strategy_meta["label"],
            "reason": reason_map.get(
                strategy_meta["value"],
                f"当前规则配置为「{strategy_meta['label']}」，已匹配负责人 {owner.username}。",
            ),
        }
    return {
        "strategy_title": strategy_meta["label"],
        "reason": f"当前规则配置为「{strategy_meta['label']}」，但未匹配到明确负责人，建议管理员介入分派。",
    }


def describe_target_owner_resolution(target_extra, owner, owner_role=""):
    owner_value = (target_extra or {}).get("target_owner_value") or "目标责任维度"
    strategy_meta = get_owner_strategy_meta(AlertRule.RuleType.TARGET, owner_role)
    if owner:
        reason_map = {
            "target_dimension": f"当前规则配置为「{strategy_meta['label']}」，已按 {owner_value} 维度匹配到负责人 {owner.username}。",
            "latest_contract_owner": f"当前规则配置为「{strategy_meta['label']}」，已回落到最近成交合同的负责人 {owner.username}。",
            "business_pool": f"当前规则配置为「{strategy_meta['label']}」，已从业务候选池匹配负责人 {owner.username}。",
            "admin_pool": f"当前规则配置为「{strategy_meta['label']}」，已分配给管理员 {owner.username} 统一统筹目标偏差。",
        }
        return {
            "strategy_title": strategy_meta["label"],
            "reason": reason_map.get(
                strategy_meta["value"],
                f"{owner_value} 的目标预警已匹配到负责人 {owner.username}。",
            ),
        }
    return {
        "strategy_title": strategy_meta["label"],
        "reason": f"当前规则配置为「{strategy_meta['label']}」，但 {owner_value} 暂未匹配到明确负责人。",
    }


def build_owner_strategy_detail(
    warning_type, contract=None, owner=None, extra=None, owner_role=""
):
    if warning_type == AlertRule.RuleType.TARGET:
        detail = describe_target_owner_resolution(extra, owner, owner_role=owner_role)
    else:
        detail = describe_contract_owner_resolution(
            contract, warning_type, owner, owner_role=owner_role
        )
    strategy_meta = get_owner_strategy_meta(warning_type, owner_role)
    detail["catalog_title"] = get_warning_type_label(warning_type)
    detail["configured_value"] = strategy_meta["value"]
    detail["configured_label"] = strategy_meta["label"]
    detail["configured_description"] = strategy_meta["description"]
    detail["recommended_value"] = strategy_meta["default_value"]
    detail["recommended_label"] = strategy_meta["default_label"]
    detail["uses_default"] = strategy_meta["is_default"]
    return detail


def build_trigger_summary(warning_type, contract=None, due_date=None, extra=None):
    extra = extra or {}
    if warning_type == AlertRule.RuleType.PAYMENT:
        return f"付款节点 {extra.get('phase') or '-'} 截止于 {due_date or '-'}，触发付款到期规则。"
    if warning_type == AlertRule.RuleType.DELIVERY:
        return f"交付节点 {extra.get('milestone_name') or '-'} 计划于 {due_date or '-'} 完成，当前仍未完成。"
    if warning_type == AlertRule.RuleType.CONTRACT:
        return f"合同 {contract.contract_no if contract else '-'} 将于 {due_date or '-'} 到期，且续签状态未完成。"
    if warning_type == AlertRule.RuleType.INVOICE:
        return f"付款节点 {extra.get('phase') or '-'} 截止于 {due_date or '-'}，当前发票状态仍为待开具。"
    if warning_type == AlertRule.RuleType.TARGET:
        return (
            f"{extra.get('target_owner_value') or '-'} 当前达成率 "
            f"{extra.get('progress') or 0}% ，低于阈值 {extra.get('warning_threshold') or 0}% 。"
        )
    return "命中预警规则。"


def get_warning_type_from_target(target):
    if not target:
        return ""
    if not str(target).startswith("alert:"):
        return ""
    try:
        alert_id = int(str(target).split(":", 1)[1])
    except (TypeError, ValueError):
        return ""
    return (
        AlertMessage.objects.filter(id=alert_id)
        .values_list("warning_type", flat=True)
        .first()
        or ""
    )


def get_client_ip(request):
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        return x_forwarded_for.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


def create_operation_log(
    request, action, target, detail, before_data=None, after_data=None, status_code=200
):
    if not getattr(request, "user", None) or not request.user.is_authenticated:
        return
    OperationLog.objects.create(
        user=request.user,
        ip_address=get_client_ip(request),
        action=action,
        target=target,
        detail=detail,
        before_data=before_data or {},
        after_data=after_data or {},
        method=request.method,
        path=request.path,
        status_code=status_code,
    )


def build_contract_snapshot(contract):
    if not contract:
        return None
    return {
        "id": contract.id,
        "contract_no": contract.contract_no,
        "title": contract.title,
        "client_name": contract.client_name,
        "amount": str(contract.amount or 0),
        "currency": contract.currency,
        "region": contract.region,
        "department": contract.department,
        "salesperson": contract.salesperson,
        "status": contract.status,
        "status_display": contract.get_status_display(),
        "payment_status": contract.payment_status,
        "payment_status_display": contract.get_payment_status_display(),
        "delivery_status": contract.delivery_status,
        "delivery_status_display": contract.get_delivery_status_display(),
        "renewal_status": contract.renewal_status,
        "renewal_status_display": contract.get_renewal_status_display(),
        "end_date": contract.end_date,
        "created_by_name": contract.created_by.username if contract.created_by else "",
        "renewal_owner_name": (
            contract.renewal_owner.username if contract.renewal_owner else ""
        ),
    }


def build_alert_detail_data(alert):
    data = AlertMessageSerializer(alert).data
    trigger_summary = build_trigger_summary(
        warning_type=alert.warning_type,
        contract=alert.contract,
        due_date=alert.due_date,
        extra={},
    )
    owner_strategy = build_owner_strategy_detail(
        warning_type=alert.warning_type,
        contract=alert.contract,
        owner=alert.owner,
        extra={},
        owner_role=alert.rule.owner_role if alert.rule else "",
    )
    data["contract_snapshot"] = build_contract_snapshot(alert.contract)
    data["owner_strategy"] = owner_strategy
    data["trigger_summary"] = trigger_summary
    recent_logs = OperationLog.objects.filter(target=f"alert:{alert.id}").order_by(
        "-created_at"
    )[:5]
    data["recent_logs"] = [
        {
            "id": item.id,
            "action": item.action,
            "detail": item.detail,
            "username": item.user.username if item.user else "",
            "created_at": item.created_at,
        }
        for item in recent_logs
    ]
    timeline = [
        {
            "stage": "created",
            "title": "预警生成",
            "time": alert.created_at,
            "description": trigger_summary,
        },
        {
            "stage": "assignment",
            "title": "负责人匹配",
            "time": alert.created_at,
            "description": owner_strategy.get("reason") or "系统完成负责人匹配。",
        },
    ]
    if alert.due_date:
        timeline.append(
            {
                "stage": "deadline",
                "title": "截止节点",
                "time": alert.due_date,
                "description": f"该预警要求在 {alert.due_date} 前完成跟进处理。",
            }
        )
    for item in reversed(data["recent_logs"]):
        timeline.append(
            {
                "stage": "operation",
                "title": item["detail"],
                "time": item["created_at"],
                "description": f"{item['username'] or '系统'} 执行了该操作。",
            }
        )
    if alert.status == AlertMessage.Status.PROCESSED and alert.processed_at:
        timeline.append(
            {
                "stage": "resolved",
                "title": "预警已处理",
                "time": alert.processed_at,
                "description": f"{alert.processed_by.username if alert.processed_by else '系统'} 已完成该预警处置。",
            }
        )
    data["timeline"] = timeline
    return data


def serialize_preview_owner(owner):
    if not owner:
        return {
            "id": None,
            "username": "",
            "role": "",
            "department": "",
            "region": "",
        }
    return {
        "id": owner.id,
        "username": owner.username,
        "role": owner.role,
        "department": owner.department,
        "region": owner.region,
    }


def build_preview_item(
    rule,
    contract,
    title,
    content,
    due_date,
    owner,
    extra=None,
    existing_pending=False,
    owner_role="",
):
    return {
        "rule_id": rule.id if rule else None,
        "rule_name": rule.name if rule else "",
        "warning_type": rule.rule_type if rule else "",
        "title": title,
        "content": content,
        "contract_id": contract.id if contract else None,
        "contract_no": contract.contract_no if contract else "",
        "due_date": due_date,
        "level": rule.level if rule else "medium",
        "owner": serialize_preview_owner(owner),
        "owner_strategy": build_owner_strategy_detail(
            warning_type=rule.rule_type if rule else "",
            contract=contract,
            owner=owner,
            extra=extra,
            owner_role=owner_role if rule else "",
        ),
        "trigger_summary": build_trigger_summary(
            warning_type=rule.rule_type if rule else "",
            contract=contract,
            due_date=due_date,
            extra=extra,
        ),
        "existing_pending": existing_pending,
        "extra": extra or {},
    }


def collect_alert_scan_preview(
    limit=80, rule_type=None, only_creatable=False, owner_role_overrides=None
):
    today = timezone.now().date()
    rules = AlertRule.objects.filter(is_active=True)
    if rule_type:
        rules = rules.filter(rule_type=rule_type)
    owner_role_overrides = owner_role_overrides or {}
    preview_items = []
    type_counts = {
        AlertRule.RuleType.PAYMENT: 0,
        AlertRule.RuleType.DELIVERY: 0,
        AlertRule.RuleType.CONTRACT: 0,
        AlertRule.RuleType.INVOICE: 0,
        AlertRule.RuleType.TARGET: 0,
    }
    creatable_counts = {key: 0 for key in type_counts}

    def append_item(
        rule, contract, title, content, due_date, owner, extra=None, owner_role=""
    ):
        nonlocal preview_items
        existing_pending = AlertMessage.objects.filter(
            contract=contract,
            rule=rule,
            title=title,
            status=AlertMessage.Status.PENDING,
        ).exists()
        type_counts[rule.rule_type] = type_counts.get(rule.rule_type, 0) + 1
        if not existing_pending:
            creatable_counts[rule.rule_type] = (
                creatable_counts.get(rule.rule_type, 0) + 1
            )
        if only_creatable and existing_pending:
            return
        if len(preview_items) < limit:
            preview_items.append(
                build_preview_item(
                    rule=rule,
                    contract=contract,
                    title=title,
                    content=content,
                    due_date=due_date,
                    owner=owner,
                    extra=extra,
                    existing_pending=existing_pending,
                    owner_role=owner_role,
                )
            )

    for rule in rules:
        effective_owner_role = owner_role_overrides.get(rule.rule_type, rule.owner_role)
        threshold_date = today + timedelta(days=rule.remind_days)
        if rule.rule_type == AlertRule.RuleType.PAYMENT:
            plans = PaymentPlan.objects.filter(
                paid_date__isnull=True, due_date__lte=threshold_date
            ).select_related(
                "contract", "contract__created_by", "contract__renewal_owner"
            )
            for plan in plans:
                append_item(
                    rule=rule,
                    contract=plan.contract,
                    title=f"付款预警 - {plan.contract.contract_no}",
                    content=f"付款节点「{plan.phase}」将于 {plan.due_date} 到期",
                    due_date=plan.due_date,
                    owner=resolve_contract_alert_owner(
                        plan.contract,
                        AlertRule.RuleType.PAYMENT,
                        owner_role=effective_owner_role,
                    ),
                    extra={"phase": plan.phase},
                    owner_role=effective_owner_role,
                )
        elif rule.rule_type == AlertRule.RuleType.DELIVERY:
            milestones = (
                ContractMilestone.objects.filter(
                    node_type=ContractMilestone.NodeType.DELIVERY,
                    planned_date__lte=threshold_date,
                )
                .exclude(status=ContractMilestone.Status.COMPLETED)
                .select_related(
                    "contract", "contract__created_by", "contract__renewal_owner"
                )
            )
            for milestone in milestones:
                append_item(
                    rule=rule,
                    contract=milestone.contract,
                    title=f"交付预警 - {milestone.contract.contract_no}",
                    content=f"交付节点「{milestone.name}」计划于 {milestone.planned_date} 完成",
                    due_date=milestone.planned_date,
                    owner=resolve_contract_alert_owner(
                        milestone.contract,
                        AlertRule.RuleType.DELIVERY,
                        owner_role=effective_owner_role,
                    ),
                    extra={"milestone_name": milestone.name},
                    owner_role=effective_owner_role,
                )
        elif rule.rule_type == AlertRule.RuleType.CONTRACT:
            contracts = Contract.objects.filter(
                end_date__isnull=False, end_date__lte=threshold_date
            ).exclude(renewal_status=Contract.RenewalStatus.RENEWED)
            for contract in contracts:
                append_item(
                    rule=rule,
                    contract=contract,
                    title=f"到期预警 - {contract.contract_no}",
                    content=f"合同将于 {contract.end_date} 到期，请及时跟进续签",
                    due_date=contract.end_date,
                    owner=resolve_contract_alert_owner(
                        contract,
                        AlertRule.RuleType.CONTRACT,
                        owner_role=effective_owner_role,
                    ),
                    extra={"renewal_status": contract.renewal_status},
                    owner_role=effective_owner_role,
                )
        elif rule.rule_type == AlertRule.RuleType.INVOICE:
            plans = PaymentPlan.objects.filter(
                invoice_status=PaymentPlan.InvoiceStatus.PENDING,
                due_date__lte=threshold_date,
            ).select_related(
                "contract", "contract__created_by", "contract__renewal_owner"
            )
            for plan in plans:
                append_item(
                    rule=rule,
                    contract=plan.contract,
                    title=f"发票预警 - {plan.contract.contract_no}",
                    content=f"付款节点「{plan.phase}」尚未开票",
                    due_date=plan.due_date,
                    owner=resolve_contract_alert_owner(
                        plan.contract,
                        AlertRule.RuleType.INVOICE,
                        owner_role=effective_owner_role,
                    ),
                    extra={"phase": plan.phase},
                    owner_role=effective_owner_role,
                )
        elif rule.rule_type == AlertRule.RuleType.TARGET:
            for target in SalesTarget.objects.all():
                related_contracts = Contract.objects.filter(
                    sign_date__gte=target.start_date, sign_date__lte=target.end_date
                )
                if target.target_type == SalesTarget.TargetType.SALESPERSON:
                    related_contracts = related_contracts.filter(
                        salesperson=target.owner_value
                    )
                elif target.target_type == SalesTarget.TargetType.DEPARTMENT:
                    related_contracts = related_contracts.filter(
                        department=target.owner_value
                    )
                elif target.target_type == SalesTarget.TargetType.REGION:
                    related_contracts = related_contracts.filter(
                        region=target.owner_value
                    )
                actual_amount = related_contracts.aggregate(total=Sum("base_amount"))[
                    "total"
                ] or Decimal("0")
                progress = (
                    float(actual_amount / target.target_amount * 100)
                    if target.target_amount
                    else 0
                )
                if progress < float(target.warning_threshold):
                    append_item(
                        rule=rule,
                        contract=None,
                        title=f"目标预警 - {target.name}",
                        content=f"{target.owner_value} 当前达成率 {progress:.2f}%，低于阈值 {target.warning_threshold}%",
                        due_date=target.end_date,
                        owner=resolve_target_alert_owner(
                            target,
                            related_contracts,
                            owner_role=effective_owner_role,
                        ),
                        extra={
                            "target_name": target.name,
                            "target_owner_value": target.owner_value,
                            "progress": round(progress, 2),
                            "warning_threshold": float(target.warning_threshold),
                        },
                        owner_role=effective_owner_role,
                    )

    return {
        "preview_items": preview_items,
        "total_hits": sum(type_counts.values()),
        "creatable_total": sum(creatable_counts.values()),
        "type_counts": type_counts,
        "creatable_type_counts": creatable_counts,
    }


def build_preview_identity(item):
    return "|".join(
        [
            item.get("warning_type") or "",
            item.get("title") or "",
            item.get("contract_no") or "",
            str(item.get("due_date") or ""),
        ]
    )


class StandardizedAdminViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, IsAdmin]

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return success_response(data=serializer.data)

    def retrieve(self, request, *args, **kwargs):
        serializer = self.get_serializer(self.get_object())
        return success_response(data=serializer.data)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return success_response(
            data=self.get_serializer(serializer.instance).data, message="创建成功"
        )

    def update(self, request, *args, **kwargs):
        serializer = self.get_serializer(
            self.get_object(), data=request.data, partial=True
        )
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return success_response(
            data=self.get_serializer(serializer.instance).data, message="更新成功"
        )

    def destroy(self, request, *args, **kwargs):
        self.perform_destroy(self.get_object())
        return success_response(message="删除成功")


class DataPermissionRuleViewSet(StandardizedAdminViewSet):
    queryset = DataPermissionRule.objects.select_related("user").all()
    serializer_class = DataPermissionRuleSerializer


class AlertRuleViewSet(StandardizedAdminViewSet):
    queryset = AlertRule.objects.all()
    serializer_class = AlertRuleSerializer

    @action(detail=False, methods=["get"])
    def strategy_options(self, request):
        data = {
            "defaults": {
                warning_type: get_default_owner_strategy_value(warning_type)
                for warning_type in [
                    AlertRule.RuleType.PAYMENT,
                    AlertRule.RuleType.DELIVERY,
                    AlertRule.RuleType.CONTRACT,
                    AlertRule.RuleType.INVOICE,
                    AlertRule.RuleType.TARGET,
                ]
            },
            "options": {
                warning_type: get_owner_strategy_options(warning_type)
                for warning_type in [
                    AlertRule.RuleType.PAYMENT,
                    AlertRule.RuleType.DELIVERY,
                    AlertRule.RuleType.CONTRACT,
                    AlertRule.RuleType.INVOICE,
                    AlertRule.RuleType.TARGET,
                ]
            },
            "catalog": get_owner_strategy_catalog(),
        }
        return success_response(data=data)

    @action(detail=False, methods=["get"])
    def preview_impact(self, request):
        rule_type = request.query_params.get("rule_type") or ""
        owner_role = request.query_params.get("owner_role") or ""
        only_creatable = request.query_params.get("only_creatable") == "true"
        if not rule_type:
            return error_response(message="请选择要预览的规则类型", code=400)

        current_preview = collect_alert_scan_preview(
            limit=120,
            rule_type=rule_type,
            only_creatable=only_creatable,
        )
        proposed_preview = collect_alert_scan_preview(
            limit=120,
            rule_type=rule_type,
            only_creatable=only_creatable,
            owner_role_overrides={rule_type: owner_role},
        )

        current_map = {
            build_preview_identity(item): item
            for item in current_preview["preview_items"]
        }
        proposed_map = {
            build_preview_identity(item): item
            for item in proposed_preview["preview_items"]
        }
        compare_items = []
        changed_count = 0

        for identity in proposed_map:
            current_item = current_map.get(identity)
            proposed_item = proposed_map[identity]
            current_owner = (current_item or {}).get("owner") or {}
            proposed_owner = proposed_item.get("owner") or {}
            changed = current_owner.get("id") != proposed_owner.get("id")
            if changed:
                changed_count += 1
            compare_items.append(
                {
                    "warning_type": proposed_item.get("warning_type"),
                    "title": proposed_item.get("title"),
                    "contract_no": proposed_item.get("contract_no"),
                    "due_date": proposed_item.get("due_date"),
                    "existing_pending": proposed_item.get("existing_pending"),
                    "changed": changed,
                    "current_owner": current_owner,
                    "current_strategy": (current_item or {}).get("owner_strategy")
                    or {},
                    "proposed_owner": proposed_owner,
                    "proposed_strategy": proposed_item.get("owner_strategy") or {},
                    "trigger_summary": proposed_item.get("trigger_summary") or "",
                }
            )

        compare_items.sort(
            key=lambda item: (
                0 if item["changed"] else 1,
                item.get("due_date") or "",
                item.get("title") or "",
            )
        )
        strategy_meta = get_owner_strategy_meta(rule_type, owner_role)
        current_rule = (
            AlertRule.objects.filter(rule_type=rule_type).order_by("id").first()
        )
        current_meta = get_owner_strategy_meta(
            rule_type, current_rule.owner_role if current_rule else ""
        )
        data = {
            "rule_type": rule_type,
            "only_creatable": only_creatable,
            "total_hits": proposed_preview["total_hits"],
            "changed_count": changed_count,
            "unchanged_count": max(len(compare_items) - changed_count, 0),
            "current_strategy": current_meta,
            "proposed_strategy": strategy_meta,
            "compare_items": compare_items[:40],
        }
        return success_response(data=data)


class AlertMessageViewSet(StandardizedAdminViewSet):
    queryset = AlertMessage.objects.select_related(
        "contract", "rule", "owner", "processed_by"
    ).all()
    serializer_class = AlertMessageSerializer

    @action(detail=True, methods=["post"])
    def process(self, request, pk=None):
        alert = self.get_object()
        alert.status = AlertMessage.Status.PROCESSED
        alert.processed_by = request.user
        alert.processed_at = timezone.now()
        alert.save(update_fields=["status", "processed_by", "processed_at"])
        return success_response(
            data=AlertMessageSerializer(alert).data, message="预警已处理"
        )

    @action(detail=False, methods=["post"])
    def scan(self, request):
        preview_data = collect_alert_scan_preview(limit=120)
        created_count = 0
        recent_created = []
        created_type_counts = {
            key: 0 for key in preview_data["creatable_type_counts"].keys()
        }

        rule_map = {rule.id: rule for rule in AlertRule.objects.filter(is_active=True)}
        contract_ids = [
            item["contract_id"]
            for item in preview_data["preview_items"]
            if item["contract_id"]
        ]
        owner_ids = [
            item["owner"]["id"]
            for item in preview_data["preview_items"]
            if item["owner"] and item["owner"]["id"]
        ]
        contract_map = Contract.objects.in_bulk(contract_ids)
        owner_map = User.objects.in_bulk(owner_ids)

        for item in preview_data["preview_items"]:
            if item["existing_pending"]:
                continue
            rule = rule_map.get(item["rule_id"])
            if not rule:
                continue
            contract = contract_map.get(item["contract_id"])
            owner = owner_map.get(item["owner"]["id"]) if item.get("owner") else None
            AlertMessage.objects.create(
                contract=contract,
                rule=rule,
                title=item["title"],
                content=item["content"],
                warning_type=item["warning_type"],
                level=item["level"],
                owner=owner,
                due_date=item["due_date"],
            )
            created_count += 1
            created_type_counts[rule.rule_type] = (
                created_type_counts.get(rule.rule_type, 0) + 1
            )
            if len(recent_created) < 5:
                recent_created.append(
                    {
                        "title": item["title"],
                        "warning_type": item["warning_type"],
                        "contract_no": item["contract_no"],
                        "owner_name": (
                            item["owner"]["username"] if item["owner"] else ""
                        ),
                    }
                )

        response_data = {
            "created_count": created_count,
            "created_type_counts": created_type_counts,
            "recent_created": recent_created,
        }
        create_operation_log(
            request,
            action="ALERT_SCAN",
            target="alerts:scan",
            detail=f"执行预警扫描，新增 {created_count} 条消息",
            after_data=response_data,
        )
        return success_response(data=response_data, message="预警扫描完成")

    @action(detail=False, methods=["get"])
    def scan_preview(self, request):
        preview_data = collect_alert_scan_preview(
            limit=60,
            rule_type=request.query_params.get("rule_type") or None,
            only_creatable=request.query_params.get("only_creatable") == "true",
        )
        return success_response(
            data={
                "total_hits": preview_data["total_hits"],
                "creatable_total": preview_data["creatable_total"],
                "type_counts": preview_data["type_counts"],
                "creatable_type_counts": preview_data["creatable_type_counts"],
                "preview_items": preview_data["preview_items"],
                "strategy_catalog": get_owner_strategy_catalog(),
            }
        )

    @action(detail=False, methods=["get"])
    def scan_preview_export(self, request):
        preview_data = collect_alert_scan_preview(
            limit=500,
            rule_type=request.query_params.get("rule_type") or None,
            only_creatable=request.query_params.get("only_creatable") == "true",
        )
        response = HttpResponse(content_type="text/csv; charset=utf-8")
        response["Content-Disposition"] = (
            'attachment; filename="alert-scan-preview.csv"'
        )
        response.write("\ufeff")
        writer = csv.writer(response)
        writer.writerow(
            [
                "预警类型",
                "规则名称",
                "预警标题",
                "合同编号",
                "负责人",
                "负责人策略",
                "触发说明",
                "截止时间",
                "状态",
            ]
        )
        for item in preview_data["preview_items"]:
            writer.writerow(
                [
                    get_warning_type_label(item["warning_type"]),
                    item["rule_name"],
                    item["title"],
                    item["contract_no"],
                    (item.get("owner") or {}).get("username", ""),
                    (item.get("owner_strategy") or {}).get("strategy_title", ""),
                    item.get("trigger_summary", ""),
                    item.get("due_date") or "",
                    "已存在待处理" if item.get("existing_pending") else "将新建",
                ]
            )
        return response

    @action(detail=False, methods=["get"])
    def scan_summary(self, request):
        params = request.query_params
        warning_type = params.get("warning_type")
        action = params.get("action")
        operator = params.get("operator")
        date_from = params.get("date_from")
        date_to = params.get("date_to")
        queryset = AlertMessage.objects.select_related("owner").all()
        if warning_type:
            queryset = queryset.filter(warning_type=warning_type)
        pending_queryset = queryset.filter(status=AlertMessage.Status.PENDING)
        recent_scan_logs = OperationLog.objects.filter(target="alerts:scan")
        recent_assignment_logs = OperationLog.objects.filter(
            action__in=["ALERT_REASSIGN", "ALERT_PROCESS"]
        )
        if action:
            recent_assignment_logs = recent_assignment_logs.filter(action=action)
        if operator:
            recent_assignment_logs = recent_assignment_logs.filter(user_id=operator)
            recent_scan_logs = recent_scan_logs.filter(user_id=operator)
        if date_from:
            recent_assignment_logs = recent_assignment_logs.filter(
                created_at__date__gte=date_from
            )
            recent_scan_logs = recent_scan_logs.filter(created_at__date__gte=date_from)
        if date_to:
            recent_assignment_logs = recent_assignment_logs.filter(
                created_at__date__lte=date_to
            )
            recent_scan_logs = recent_scan_logs.filter(created_at__date__lte=date_to)
        if warning_type:
            alert_ids = list(
                AlertMessage.objects.filter(warning_type=warning_type).values_list(
                    "id", flat=True
                )
            )
            recent_assignment_logs = recent_assignment_logs.filter(
                target__in=[f"alert:{alert_id}" for alert_id in alert_ids]
            )
        recent_scan_logs = recent_scan_logs.order_by("-created_at")[:5]
        recent_assignment_logs = recent_assignment_logs.order_by("-created_at")[:8]
        data = {
            "pending_total": pending_queryset.count(),
            "processed_total": queryset.filter(
                status=AlertMessage.Status.PROCESSED
            ).count(),
            "type_counts": {
                "payment_due": pending_queryset.filter(
                    warning_type=AlertRule.RuleType.PAYMENT
                ).count(),
                "delivery_due": pending_queryset.filter(
                    warning_type=AlertRule.RuleType.DELIVERY
                ).count(),
                "contract_expiry": pending_queryset.filter(
                    warning_type=AlertRule.RuleType.CONTRACT
                ).count(),
                "invoice_due": pending_queryset.filter(
                    warning_type=AlertRule.RuleType.INVOICE
                ).count(),
                "target_progress": pending_queryset.filter(
                    warning_type=AlertRule.RuleType.TARGET
                ).count(),
            },
            "recent_scans": [
                {
                    "id": item.id,
                    "detail": item.detail,
                    "username": item.user.username if item.user else "",
                    "created_at": item.created_at,
                    "after_data": item.after_data,
                }
                for item in recent_scan_logs
            ],
            "recent_actions": [
                {
                    "id": item.id,
                    "action": item.action,
                    "target": item.target,
                    "detail": item.detail,
                    "username": item.user.username if item.user else "",
                    "warning_type": get_warning_type_from_target(item.target),
                    "created_at": item.created_at,
                }
                for item in recent_assignment_logs
            ],
            "strategy_catalog": get_owner_strategy_catalog(),
        }
        return success_response(data=data)


class AlertCenterView(APIView):
    permission_classes = [IsAuthenticated, IsViewer]

    def get_queryset(self, request):
        queryset = AlertMessage.objects.select_related(
            "contract", "rule", "owner", "processed_by"
        )
        if request.user.role == "admin":
            return queryset
        return queryset.filter(
            Q(owner=request.user)
            | Q(owner__isnull=True, warning_type=AlertRule.RuleType.TARGET)
        )

    def get(self, request):
        queryset = self.get_queryset(request)
        pending_queryset = queryset.filter(status=AlertMessage.Status.PENDING)
        recent_alerts = pending_queryset[:5]
        level_counts = {
            "high": pending_queryset.filter(level="high").count(),
            "medium": pending_queryset.filter(level="medium").count(),
            "low": pending_queryset.filter(level="low").count(),
        }
        data = {
            "pending_count": pending_queryset.count(),
            "processed_count": queryset.filter(
                status=AlertMessage.Status.PROCESSED
            ).count(),
            "level_counts": level_counts,
            "recent_alerts": AlertMessageSerializer(recent_alerts, many=True).data,
        }
        return success_response(data=data)


class AlertCenterProcessView(APIView):
    permission_classes = [IsAuthenticated, IsViewer]

    def post(self, request, pk):
        queryset = AlertMessage.objects.select_related("owner")
        if request.user.role != "admin":
            queryset = queryset.filter(owner=request.user)
        alert = queryset.filter(pk=pk).first()
        if not alert:
            return error_response(message="未找到可处理的预警消息", code=400)
        if alert.status == AlertMessage.Status.PROCESSED:
            return success_response(
                data=AlertMessageSerializer(alert).data, message="预警已处理"
            )
        alert.status = AlertMessage.Status.PROCESSED
        alert.processed_by = request.user
        alert.processed_at = timezone.now()
        alert.save(update_fields=["status", "processed_by", "processed_at"])
        return success_response(
            data=AlertMessageSerializer(alert).data, message="预警已处理"
        )


class AlertWorkspaceViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    serializer_class = AlertMessageSerializer
    permission_classes = [IsAuthenticated, IsViewer]
    search_fields = ["title", "content", "contract__contract_no", "owner__username"]
    ordering_fields = ["created_at", "due_date", "level"]
    ordering = ["status", "due_date", "-created_at"]

    def get_base_queryset(self):
        queryset = AlertMessage.objects.select_related(
            "contract",
            "contract__created_by",
            "contract__renewal_owner",
            "rule",
            "owner",
            "processed_by",
        )
        if self.request.user.role == "admin":
            return queryset
        return queryset.filter(
            Q(owner=self.request.user)
            | Q(owner__isnull=True, warning_type=AlertRule.RuleType.TARGET)
        )

    def get_queryset(self):
        queryset = self.get_base_queryset()
        params = self.request.query_params

        status = params.get("status")
        level = params.get("level")
        warning_type = params.get("warning_type")
        owner = params.get("owner")
        contract_no = params.get("contract_no")
        keyword = params.get("keyword")
        due_scope = params.get("due_scope")

        if status:
            queryset = queryset.filter(status=status)
        if level:
            queryset = queryset.filter(level=level)
        if warning_type:
            queryset = queryset.filter(warning_type=warning_type)
        if owner and self.request.user.role == "admin":
            queryset = queryset.filter(owner_id=owner)
        if contract_no:
            queryset = queryset.filter(contract__contract_no__icontains=contract_no)
        if keyword:
            queryset = queryset.filter(
                Q(title__icontains=keyword)
                | Q(content__icontains=keyword)
                | Q(contract__contract_no__icontains=keyword)
                | Q(owner__username__icontains=keyword)
            )

        today = timezone.now().date()
        if due_scope == "today":
            queryset = queryset.filter(due_date=today)
        elif due_scope == "7d":
            queryset = queryset.filter(
                due_date__isnull=False, due_date__lte=today + timedelta(days=7)
            )
        elif due_scope == "overdue":
            queryset = queryset.filter(
                due_date__isnull=False,
                due_date__lt=today,
                status=AlertMessage.Status.PENDING,
            )

        return queryset

    def retrieve(self, request, *args, **kwargs):
        alert = self.get_queryset().filter(pk=kwargs.get("pk")).first()
        if not alert:
            return error_response(message="未找到预警详情", code=400)
        return success_response(data=build_alert_detail_data(alert))

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return success_response(data=serializer.data)

    @action(detail=False, methods=["get"])
    def summary(self, request):
        queryset = self.get_base_queryset()
        pending_queryset = queryset.filter(status=AlertMessage.Status.PENDING)
        today = timezone.now().date()
        data = {
            "total_count": queryset.count(),
            "pending_count": pending_queryset.count(),
            "processed_count": queryset.filter(
                status=AlertMessage.Status.PROCESSED
            ).count(),
            "high_count": pending_queryset.filter(level="high").count(),
            "overdue_count": pending_queryset.filter(
                due_date__isnull=False, due_date__lt=today
            ).count(),
            "today_count": pending_queryset.filter(due_date=today).count(),
            "week_count": pending_queryset.filter(
                due_date__isnull=False, due_date__lte=today + timedelta(days=7)
            ).count(),
        }
        return success_response(data=data)

    @action(detail=False, methods=["get"])
    def assignees(self, request):
        queryset = get_business_users()
        keyword = request.query_params.get("keyword")
        if keyword:
            queryset = queryset.filter(
                Q(username__icontains=keyword)
                | Q(department__icontains=keyword)
                | Q(region__icontains=keyword)
            )
        data = [
            {
                "id": user.id,
                "username": user.username,
                "role": user.role,
                "department": user.department,
                "region": user.region,
            }
            for user in queryset[:50]
        ]
        return success_response(data=data)

    @action(detail=True, methods=["post"])
    def process(self, request, pk=None):
        alert = self.get_queryset().filter(pk=pk).first()
        if not alert:
            return error_response(message="未找到可处理的预警消息", code=400)
        if alert.status == AlertMessage.Status.PROCESSED:
            return success_response(
                data=AlertMessageSerializer(alert).data, message="预警已处理"
            )
        alert.status = AlertMessage.Status.PROCESSED
        alert.processed_by = request.user
        alert.processed_at = timezone.now()
        alert.save(update_fields=["status", "processed_by", "processed_at"])
        create_operation_log(
            request,
            action="ALERT_PROCESS",
            target=f"alert:{alert.id}",
            detail=f"处理预警《{alert.title}》",
            before_data={"status": AlertMessage.Status.PENDING},
            after_data={"status": AlertMessage.Status.PROCESSED},
        )
        return success_response(
            data=AlertMessageSerializer(alert).data, message="预警已处理"
        )

    @action(detail=False, methods=["post"])
    def batch_process(self, request):
        ids = request.data.get("ids") or []
        if not isinstance(ids, list) or not ids:
            return error_response(message="请至少选择一条预警消息", code=400)
        queryset = self.get_queryset().filter(
            id__in=ids, status=AlertMessage.Status.PENDING
        )
        updated_count = queryset.update(
            status=AlertMessage.Status.PROCESSED,
            processed_by=request.user,
            processed_at=timezone.now(),
        )
        return success_response(
            data={"updated_count": updated_count}, message="批量处理完成"
        )

    @action(detail=True, methods=["post"])
    def reassign(self, request, pk=None):
        if request.user.role != User.Role.ADMIN:
            return error_response(message="仅管理员可重分派预警", code=400)

        owner_id = request.data.get("owner")
        if not owner_id:
            return error_response(message="请选择新的负责人", code=400)

        owner = get_business_users().filter(pk=owner_id).first()
        if not owner:
            return error_response(message="未找到可分派的负责人", code=400)

        alert = self.get_base_queryset().filter(pk=pk).first()
        if not alert:
            return error_response(message="未找到可分派的预警", code=400)

        before_owner = alert.owner.username if alert.owner else ""
        alert.owner = owner
        alert.save(update_fields=["owner"])
        create_operation_log(
            request,
            action="ALERT_REASSIGN",
            target=f"alert:{alert.id}",
            detail=f"将预警《{alert.title}》改派给 {owner.username}",
            before_data={"owner_name": before_owner},
            after_data={"owner_name": owner.username},
        )
        return success_response(
            data=self.get_serializer(alert).data, message="负责人已更新"
        )


class SalesTargetViewSet(StandardizedAdminViewSet):
    queryset = SalesTarget.objects.all()
    serializer_class = SalesTargetSerializer


class DashboardConfigViewSet(StandardizedAdminViewSet):
    queryset = DashboardConfig.objects.select_related("created_by").all()
    serializer_class = DashboardConfigSerializer

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class DataTemplateViewSet(StandardizedAdminViewSet):
    queryset = DataTemplate.objects.all()
    serializer_class = DataTemplateSerializer


class CurrencyRateViewSet(StandardizedAdminViewSet):
    queryset = CurrencyRate.objects.all()
    serializer_class = CurrencyRateSerializer


class StampTaxRuleViewSet(StandardizedAdminViewSet):
    queryset = StampTaxRule.objects.all()
    serializer_class = StampTaxRuleSerializer


class MobileDashboardView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        config = (
            DashboardConfig.objects.filter(is_mobile=True, is_active=True)
            .order_by("-updated_at")
            .first()
        )
        contracts = Contract.objects.all()
        data = {
            "config": DashboardConfigSerializer(config).data if config else None,
            "summary": {
                "total_contracts": contracts.count(),
                "total_amount": str(
                    contracts.aggregate(total=Sum("base_amount"))["total"] or 0
                ),
                "pending_alerts": AlertMessage.objects.filter(
                    status=AlertMessage.Status.PENDING
                ).count(),
                "expiring_contracts": contracts.filter(
                    end_date__isnull=False,
                    end_date__lte=timezone.now().date() + timedelta(days=30),
                ).count(),
            },
        }
        return success_response(data=data)
