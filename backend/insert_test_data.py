#!/usr/bin/env python3
import os
import django
import random
from datetime import datetime, timedelta
from decimal import Decimal
from django.utils import timezone

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "contract_vision.settings.development")
django.setup()

from apps.users.models import User
from apps.contracts.models import (
    ApprovalProcess,
    ApprovalRequest,
    Contract,
    ContractChangeLog,
    ContractChangeRequest,
    ContractMilestone,
    PaymentPlan,
)
from apps.contracts.services import update_contract_metrics
from apps.system.models import (
    AlertMessage,
    AlertRule,
    CurrencyRate,
    DashboardConfig,
    DataPermissionRule,
    DataTemplate,
    SalesTarget,
    StampTaxRule,
)


def create_users():
    print("Creating users...")
    users = []

    admin, _ = User.objects.get_or_create(
        username="admin",
        defaults={
            "email": "admin@contractvision.com",
            "phone": "13800138000",
            "company_name": "ContractVision 系统管理员",
            "department": "管理中心",
            "region": "全国",
            "role": "admin",
            "is_superuser": True,
            "is_staff": True,
        },
    )
    admin.set_password("Admin@123")
    admin.save()
    users.append(admin)

    for i in range(1, 6):
        user, _ = User.objects.get_or_create(
            username=f"operator{i}",
            defaults={
                "email": f"operator{i}@company.com",
                "phone": f"139{i:08d}",
                "company_name": "华东科技集团",
                "department": random.choice(["销售一部", "销售二部", "大客户部"]),
                "region": random.choice(["华东", "华南", "华北"]),
                "role": "operator",
            },
        )
        user.set_password("Operator@123")
        user.save()
        users.append(user)

    for i in range(1, 4):
        user, _ = User.objects.get_or_create(
            username=f"viewer{i}",
            defaults={
                "email": f"viewer{i}@company.com",
                "phone": f"137{i:08d}",
                "company_name": "华东科技集团",
                "department": "经营分析部",
                "region": "全国",
                "role": "viewer",
            },
        )
        user.set_password("Viewer@123")
        user.save()
        users.append(user)

    print(f"Created {len(users)} users")
    return users


def create_contracts(users):
    print("Creating contracts...")
    business_users = [user for user in users if user.role in ["admin", "operator"]]
    renewal_users = [
        user for user in users if user.role == "operator"
    ] or business_users
    clients = [
        "华为技术有限公司",
        "阿里巴巴集团",
        "腾讯科技",
        "字节跳动",
        "京东集团",
        "美团点评",
        "小米科技",
        "网易公司",
        "百度在线",
        "滴滴出行",
        "美团外卖",
        "拼多多",
        "携程旅行",
        "京东商城",
        "阿里巴巴国际",
        "华为云服务",
        "腾讯云",
        "阿里云",
        "百度云",
        "腾讯游戏",
        "网易游戏",
        "京东金融",
        "蚂蚁金服",
        "腾讯支付",
        "百度金融",
        "美团金融",
        "京东支付",
        "支付宝",
    ]
    products = [
        "云服务",
        "SaaS软件",
        "数据平台",
        "企业ERP",
        "CRM系统",
        "OA办公",
        "电商平台",
        "数据分析",
        "云存储",
        "人工智能",
        "大数据平台",
        "物联网",
    ]
    regions = ["华东", "华南", "华北", "华中", "西南", "西北", "东北"]
    departments = ["销售一部", "销售二部", "销售三部", "大客户部", "电商部"]
    salespersons = ["张三", "李四", "王五", "赵六", "钱七", "孙八", "周九", "吴十"]
    statuses = ["draft", "active", "completed", "terminated", "voided"]
    payment_statuses = ["unpaid", "partial", "paid"]
    delivery_statuses = ["pending", "in_progress", "delivered"]
    currencies = ["CNY", "USD", "EUR"]

    contracts = []
    for i in range(1, 31):
        client = random.choice(clients)
        product = random.choice(products)
        region = random.choice(regions)
        department = random.choice(departments)
        salesperson = random.choice(salespersons)
        status = random.choice(statuses)
        payment_status = random.choice(payment_statuses)
        delivery_status = random.choice(delivery_statuses)
        currency = random.choice(currencies)
        amount = Decimal(f"{random.randint(1, 500)}.{random.randint(0, 99)}")
        sign_date = datetime.now().date() - timedelta(days=random.randint(1, 365))
        start_date = sign_date + timedelta(days=random.randint(1, 30))
        end_date = start_date + timedelta(days=random.randint(90, 730))

        contract, _ = Contract.objects.get_or_create(
            contract_no=f"CV{datetime.now().year}{i:06d}",
            defaults={
                "title": f"{client} - {product} 采购合同",
                "client_name": client,
                "client_contact": f'{random.choice(["张经理", "王总", "李总监", "赵主管"])}',
                "contract_type": random.choice(
                    ["软件销售", "服务采购", "设备采购", "云订阅"]
                ),
                "product_type": product,
                "amount": amount,
                "currency": currency,
                "region": region,
                "sign_date": sign_date,
                "start_date": start_date,
                "end_date": end_date,
                "status": status,
                "payment_status": payment_status,
                "delivery_status": delivery_status,
                "approval_status": random.choice(["not_required", "approved"]),
                "renewal_status": random.choice(["none", "pending", "renewed"]),
                "renewal_reminder_days": random.choice([15, 30, 45]),
                "salesperson": salesperson,
                "department": department,
                "description": f"{client} 与我司签订的{product}采购合同，合同金额{amount}元。",
                "created_by": random.choice(business_users) if business_users else None,
                "renewal_owner": (
                    random.choice(renewal_users) if renewal_users else None
                ),
            },
        )
        update_contract_metrics(contract)
        contracts.append(contract)

    print(f"Created {len(contracts)} contracts")
    return contracts


def create_contract_related_data(contracts, users):
    print("Creating milestones, payment plans and changes...")
    admin = next((user for user in users if user.role == "admin"), None)
    for index, contract in enumerate(contracts, start=1):
        if not contract.payment_plans.exists():
            for phase_index, phase_name in enumerate(
                ["预付款", "中期款", "尾款"], start=1
            ):
                due_date = (
                    contract.start_date + timedelta(days=phase_index * 30)
                    if contract.start_date
                    else datetime.now().date()
                )
                PaymentPlan.objects.get_or_create(
                    contract=contract,
                    phase=phase_name,
                    defaults={
                        "ratio": (
                            Decimal("30.00") if phase_index < 3 else Decimal("40.00")
                        ),
                        "amount": (
                            (contract.amount or Decimal("0")) * Decimal("0.3")
                            if phase_index < 3
                            else (contract.amount or Decimal("0")) * Decimal("0.4")
                        ),
                        "actual_amount": Decimal("0.00"),
                        "due_date": due_date,
                        "status": random.choice(["pending", "paid", "overdue"]),
                        "invoice_status": random.choice(
                            ["pending", "issued", "received"]
                        ),
                        "voucher_no": f"PAY-{index:04d}-{phase_index}",
                        "remark": f"{phase_name}节点",
                    },
                )

        if not contract.milestones.exists():
            milestone_specs = [
                ("delivery", "首批交付", 35),
                ("payment", "中期回款", 30),
                ("acceptance", "客户验收", 35),
            ]
            for step_index, (node_type, name, weight) in enumerate(
                milestone_specs, start=1
            ):
                planned_date = (
                    contract.start_date + timedelta(days=step_index * 25)
                    if contract.start_date
                    else datetime.now().date()
                )
                ContractMilestone.objects.get_or_create(
                    contract=contract,
                    name=name,
                    defaults={
                        "node_type": node_type,
                        "progress_weight": weight,
                        "planned_date": planned_date,
                        "actual_date": planned_date if step_index == 1 else None,
                        "status": (
                            "completed"
                            if step_index == 1
                            else random.choice(
                                ["not_started", "in_progress", "overdue"]
                            )
                        ),
                        "remark": f"{name}进度维护记录",
                    },
                )

        if not contract.change_requests.exists():
            ContractChangeRequest.objects.get_or_create(
                contract=contract,
                title="付款条款调整",
                defaults={
                    "change_type": "core",
                    "reason": "客户需求调整账期",
                    "effective_date": datetime.now().date(),
                    "before_snapshot": {"payment_status": contract.payment_status},
                    "after_snapshot": {
                        "payment_status": "partial",
                        "description": f"{contract.description}\n已申请调整付款条款。",
                    },
                    "status": random.choice(["pending", "approved"]),
                    "requested_by": random.choice(users),
                    "approved_by": admin,
                    "approved_at": timezone.now() if admin else None,
                },
            )

        ContractChangeLog.objects.get_or_create(
            contract=contract,
            field_name="amount",
            old_value=str(contract.amount),
            new_value=str(contract.amount),
            defaults={"changed_by": admin},
        )
        update_contract_metrics(contract)


def create_governance_data(users, contracts):
    print("Creating governance, alert and configuration data...")
    admin = next((user for user in users if user.role == "admin"), None)
    business_users = [user for user in users if user.role in ["admin", "operator"]]
    operators = [user for user in users if user.role == "operator"]

    for user in users[:5]:
        DataPermissionRule.objects.get_or_create(
            user=user,
            scope_type="self" if user.role != "admin" else "all",
            defaults={
                "scope_value": user.department or user.region,
                "can_edit": user.role in ["admin", "operator"],
            },
        )

    process_specs = [
        ("合同新增审批", "create", Decimal("200000.00")),
        ("合同修改审批", "update", Decimal("300000.00")),
        ("合同删除审批", "delete", Decimal("100000.00")),
        ("合同变更审批", "change", Decimal("150000.00")),
    ]
    processes = []
    for name, action_type, min_amount in process_specs:
        process, _ = ApprovalProcess.objects.get_or_create(
            name=name,
            action_type=action_type,
            defaults={
                "min_amount": min_amount,
                "steps": [
                    {"name": "销售负责人审批", "approver_role": "operator"},
                    {"name": "管理员复核", "approver_role": "admin"},
                ],
                "created_by": admin,
            },
        )
        processes.append(process)

    for contract in contracts[:8]:
        process = random.choice(processes)
        ApprovalRequest.objects.get_or_create(
            contract=contract,
            process=process,
            action_type=process.action_type,
            title=f"{contract.contract_no} - {process.name}",
            defaults={
                "request_payload": {
                    "contract_id": contract.id,
                    "contract_no": contract.contract_no,
                },
                "status": random.choice(["pending", "approved", "rejected"]),
                "requested_by": random.choice(users),
                "reviewed_by": admin,
                "reviewed_at": timezone.now(),
                "review_logs": [
                    {
                        "step": 1,
                        "action": "seeded",
                        "reviewer": "system",
                        "time": timezone.now().strftime("%Y-%m-%d %H:%M:%S"),
                    }
                ],
            },
        )

    for code, rate in [("USD", Decimal("7.120000")), ("EUR", Decimal("7.860000"))]:
        CurrencyRate.objects.get_or_create(
            currency=code,
            effective_date=datetime.now().date(),
            defaults={
                "base_currency": "CNY",
                "rate": rate,
                "is_latest": True,
                "remark": "测试汇率",
            },
        )

    for contract_type, rate in [
        ("软件销售", Decimal("0.000300")),
        ("服务采购", Decimal("0.000500")),
        ("设备采购", Decimal("0.000300")),
    ]:
        StampTaxRule.objects.get_or_create(
            contract_type=contract_type,
            defaults={"rate": rate, "description": "默认测试税率", "is_active": True},
        )

    for name, rule_type, owner_role in [
        ("付款到期预警", "payment_due", "creator"),
        ("交付到期预警", "delivery_due", "department_operator"),
        ("合同到期预警", "contract_expiry", "renewal_owner"),
        ("发票开具预警", "invoice_due", "creator"),
        ("目标达成预警", "target_progress", "target_dimension"),
    ]:
        AlertRule.objects.get_or_create(
            name=name,
            rule_type=rule_type,
            defaults={
                "remind_days": 7,
                "owner_role": owner_role,
                "level": "medium",
                "is_active": True,
            },
        )

    warning_type_pool = [
        "contract_expiry",
        "payment_due",
        "delivery_due",
        "invoice_due",
    ]
    for index, contract in enumerate(contracts[:12], start=1):
        warning_type = warning_type_pool[(index - 1) % len(warning_type_pool)]
        if warning_type == "contract_expiry":
            owner = contract.renewal_owner or contract.created_by or admin
        elif warning_type in ["payment_due", "invoice_due"]:
            owner = contract.created_by or contract.renewal_owner or admin
        else:
            owner = next(
                (
                    user
                    for user in operators
                    if user.department == contract.department
                    or user.region == contract.region
                ),
                contract.created_by or contract.renewal_owner or admin,
            )
        status = random.choice(["pending", "pending", "processed"])
        processed_by = admin if status == "processed" else None
        processed_at = (
            timezone.now() - timedelta(days=random.randint(0, 5))
            if status == "processed"
            else None
        )
        AlertMessage.objects.get_or_create(
            contract=contract,
            title=f"关键节点提醒 - {contract.contract_no} - {index:02d}",
            defaults={
                "content": f"{contract.client_name} 合同存在 {warning_type} 风险，请在截止日前完成跟进。",
                "warning_type": warning_type,
                "level": random.choice(["low", "medium", "high"]),
                "owner": owner,
                "due_date": contract.end_date
                or datetime.now().date() + timedelta(days=15),
                "status": status,
                "processed_by": processed_by,
                "processed_at": processed_at,
            },
        )

    current_month_start = datetime.now().date().replace(day=1)
    current_month_end = current_month_start + timedelta(days=30)
    target_owner_specs = [
        (
            "销售一部",
            "department",
            next(
                (user for user in business_users if user.department == "销售一部"),
                admin,
            ),
        ),
        (
            "华东",
            "region",
            next((user for user in business_users if user.region == "华东"), admin),
        ),
    ]
    for owner_value, _, target_owner in target_owner_specs:
        AlertMessage.objects.get_or_create(
            contract=None,
            title=f"目标预警样例 - {owner_value}",
            defaults={
                "content": f"{owner_value} 当前目标达成率低于预设阈值，请尽快复盘重点客户与机会池。",
                "warning_type": "target_progress",
                "level": "high",
                "owner": target_owner,
                "due_date": current_month_end,
            },
        )

    for owner_value in ["张三", "李四", "销售一部", "华东"]:
        target_type = (
            "salesperson"
            if owner_value in ["张三", "李四"]
            else "department" if owner_value == "销售一部" else "region"
        )
        SalesTarget.objects.get_or_create(
            name=f"{owner_value}月度目标",
            owner_value=owner_value,
            defaults={
                "target_type": target_type,
                "period_type": "month",
                "period_label": current_month_start.strftime("%Y-%m"),
                "start_date": current_month_start,
                "end_date": current_month_end,
                "target_amount": Decimal("800000.00"),
                "warning_threshold": Decimal("70.00"),
            },
        )

    template_specs = [
        ("标准导入模板", "import"),
        ("标准导出模板", "export"),
        ("月度经营报表模板", "report"),
    ]
    for name, template_type in template_specs:
        DataTemplate.objects.get_or_create(
            name=name,
            template_type=template_type,
            defaults={
                "version": "v1.0",
                "field_config": [
                    {"field": "contract_no", "required": True},
                    {"field": "client_name", "required": True},
                ],
                "validation_rules": [{"field": "amount", "rule": "gt:0"}],
                "description": "系统默认模板",
            },
        )

    DashboardConfig.objects.get_or_create(
        name="经营驾驶舱-PC",
        is_mobile=False,
        defaults={
            "role_scope": "admin,viewer",
            "layout": [{"x": 0, "y": 0, "w": 6, "h": 4}],
            "widgets": [
                {
                    "id": "metric-total",
                    "type": "metric",
                    "title": "累计合同金额",
                    "metric": "amount",
                },
                {"id": "trend-01", "type": "trend", "title": "月度趋势"},
                {
                    "id": "rank-01",
                    "type": "ranking",
                    "title": "销售排行",
                    "field": "salesperson",
                },
            ],
            "created_by": admin,
        },
    )
    DashboardConfig.objects.get_or_create(
        name="经营驾驶舱-Mobile",
        is_mobile=True,
        defaults={
            "role_scope": "admin,operator,viewer",
            "layout": [{"x": 0, "y": 0, "w": 2, "h": 2}],
            "widgets": [
                {
                    "id": "mobile-metric",
                    "type": "metric",
                    "title": "累计合同金额",
                    "metric": "amount",
                }
            ],
            "created_by": admin,
        },
    )


def main():
    print("=== Inserting test data...")
    users = create_users()
    contracts = create_contracts(users)
    create_contract_related_data(contracts, users)
    create_governance_data(users, contracts)
    print("=== Done!")


if __name__ == "__main__":
    main()
