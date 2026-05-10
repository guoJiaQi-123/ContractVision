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
    Customer,
    DashboardConfig,
    DataPermissionRule,
    DataTemplate,
    Department,
    OperationLog,
    ProductType,
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


def create_departments(users):
    print("Creating departments...")
    admin = next((user for user in users if user.role == "admin"), None)
    operators = [user for user in users if user.role == "operator"]

    dept_specs = [
        {
            "code": "DP-HQ",
            "name": "总公司",
            "parent_code": None,
            "manager": admin.username if admin else "",
            "sort_order": 0,
            "description": "集团总部",
        },
        {
            "code": "DP-SALE",
            "name": "销售中心",
            "parent_code": "DP-HQ",
            "manager": operators[0].username if len(operators) > 0 else "",
            "sort_order": 1,
            "description": "负责全国销售业务",
        },
        {
            "code": "DP-SALE1",
            "name": "销售一部",
            "parent_code": "DP-SALE",
            "manager": operators[0].username if len(operators) > 0 else "",
            "sort_order": 1,
            "description": "华东区销售",
        },
        {
            "code": "DP-SALE2",
            "name": "销售二部",
            "parent_code": "DP-SALE",
            "manager": operators[1].username if len(operators) > 1 else "",
            "sort_order": 2,
            "description": "华南区销售",
        },
        {
            "code": "DP-SALE3",
            "name": "大客户部",
            "parent_code": "DP-SALE",
            "manager": operators[2].username if len(operators) > 2 else "",
            "sort_order": 3,
            "description": "重点客户维护",
        },
        {
            "code": "DP-TECH",
            "name": "技术中心",
            "parent_code": "DP-HQ",
            "manager": admin.username if admin else "",
            "sort_order": 2,
            "description": "技术研发与产品交付",
        },
        {
            "code": "DP-TECH-RD",
            "name": "研发部",
            "parent_code": "DP-TECH",
            "manager": "",
            "sort_order": 1,
            "description": "产品研发",
        },
        {
            "code": "DP-TECH-QA",
            "name": "质量部",
            "parent_code": "DP-TECH",
            "manager": "",
            "sort_order": 2,
            "description": "质量保障",
        },
        {
            "code": "DP-FIN",
            "name": "财务中心",
            "parent_code": "DP-HQ",
            "manager": admin.username if admin else "",
            "sort_order": 3,
            "description": "财务管理与审计",
        },
        {
            "code": "DP-FIN-ACC",
            "name": "会计部",
            "parent_code": "DP-FIN",
            "manager": "",
            "sort_order": 1,
            "description": "日常账务处理",
        },
        {
            "code": "DP-FIN-TAX",
            "name": "税务部",
            "parent_code": "DP-FIN",
            "manager": "",
            "sort_order": 2,
            "description": "税务筹划与申报",
        },
        {
            "code": "DP-HR",
            "name": "人力资源部",
            "parent_code": "DP-HQ",
            "manager": admin.username if admin else "",
            "sort_order": 4,
            "description": "人事管理与招聘",
        },
        {
            "code": "DP-MKT",
            "name": "市场部",
            "parent_code": "DP-HQ",
            "manager": operators[3].username if len(operators) > 3 else "",
            "sort_order": 5,
            "description": "品牌推广与市场活动",
        },
        {
            "code": "DP-LEGAL",
            "name": "法务部",
            "parent_code": "DP-HQ",
            "manager": "",
            "sort_order": 6,
            "description": "合同审核与法律事务",
        },
    ]

    code_to_instance = {}
    departments = []
    for spec in dept_specs:
        parent = (
            code_to_instance.get(spec["parent_code"]) if spec["parent_code"] else None
        )
        dept, _ = Department.objects.get_or_create(
            code=spec["code"],
            defaults={
                "name": spec["name"],
                "parent": parent,
                "manager": spec["manager"],
                "sort_order": spec["sort_order"],
                "description": spec["description"],
                "is_active": True,
            },
        )
        code_to_instance[spec["code"]] = dept
        departments.append(dept)

    print(f"  Created {len(departments)} departments")
    return departments


def create_product_types():
    print("Creating product types...")
    pt_specs = [
        {
            "code": "PT-SAAS",
            "name": "SaaS软件服务",
            "category": "digital",
            "sort_order": 1,
            "description": "基于云端的软件订阅服务",
        },
        {
            "code": "PT-ERP",
            "name": "企业ERP系统",
            "category": "digital",
            "sort_order": 2,
            "description": "企业资源计划管理系统",
        },
        {
            "code": "PT-CRM",
            "name": "CRM客户管理",
            "category": "digital",
            "sort_order": 3,
            "description": "客户关系管理系统",
        },
        {
            "code": "PT-OA",
            "name": "OA办公系统",
            "category": "digital",
            "sort_order": 4,
            "description": "办公自动化系统",
        },
        {
            "code": "PT-CLOUD",
            "name": "云服务",
            "category": "service",
            "sort_order": 5,
            "description": "云计算基础设施服务",
        },
        {
            "code": "PT-DATA",
            "name": "数据分析平台",
            "category": "service",
            "sort_order": 6,
            "description": "大数据分析与可视化平台",
        },
        {
            "code": "PT-AI",
            "name": "人工智能解决方案",
            "category": "service",
            "sort_order": 7,
            "description": "AI定制化解决方案",
        },
        {
            "code": "PT-IOT",
            "name": "物联网平台",
            "category": "service",
            "sort_order": 8,
            "description": "IoT设备接入与管理平台",
        },
        {
            "code": "PT-SERVER",
            "name": "服务器硬件",
            "category": "physical",
            "sort_order": 9,
            "description": "高性能服务器设备",
        },
        {
            "code": "PT-NETWORK",
            "name": "网络设备",
            "category": "physical",
            "sort_order": 10,
            "description": "交换机路由器等网络设备",
        },
        {
            "code": "PT-CONSULT",
            "name": "咨询服务",
            "category": "financial",
            "sort_order": 11,
            "description": "IT规划与数字化转型咨询",
        },
        {
            "code": "PT-INSURE",
            "name": "保险服务",
            "category": "financial",
            "sort_order": 12,
            "description": "商业保险方案",
        },
        {
            "code": "PT-OTHER",
            "name": "其他",
            "category": "other",
            "sort_order": 99,
            "description": "其他产品类型",
        },
    ]

    product_types = []
    for spec in pt_specs:
        pt, _ = ProductType.objects.get_or_create(
            code=spec["code"],
            defaults={
                "name": spec["name"],
                "category": spec["category"],
                "sort_order": spec["sort_order"],
                "description": spec["description"],
                "is_active": True,
            },
        )
        product_types.append(pt)

    print(f"  Created {len(product_types)} product types")
    return product_types


def create_customers():
    print("Creating customers...")
    customer_specs = [
        {
            "code": "KH-HW",
            "name": "华为技术有限公司",
            "short_name": "华为",
            "level": "vip",
            "contact": "张经理",
            "phone": "13800001001",
            "email": "zhang@huawei.com",
            "region": "华南",
            "industry": "通信",
            "address": "深圳市龙岗区坂田华为基地",
        },
        {
            "code": "KH-ALI",
            "name": "阿里巴巴集团",
            "short_name": "阿里",
            "level": "vip",
            "contact": "李总监",
            "phone": "13800001002",
            "email": "li@alibaba.com",
            "region": "华东",
            "industry": "互联网",
            "address": "杭州市余杭区文一西路",
        },
        {
            "code": "KH-TX",
            "name": "腾讯科技",
            "short_name": "腾讯",
            "level": "vip",
            "contact": "王总",
            "phone": "13800001003",
            "email": "wang@tencent.com",
            "region": "华南",
            "industry": "互联网",
            "address": "深圳市南山区科技园",
        },
        {
            "code": "KH-BD",
            "name": "百度在线",
            "short_name": "百度",
            "level": "vip",
            "contact": "赵主管",
            "phone": "13800001004",
            "email": "zhao@baidu.com",
            "region": "华北",
            "industry": "互联网",
            "address": "北京市海淀区上地十街",
        },
        {
            "code": "KH-JD",
            "name": "京东集团",
            "short_name": "京东",
            "level": "normal",
            "contact": "钱经理",
            "phone": "13800001005",
            "email": "qian@jd.com",
            "region": "华北",
            "industry": "电商",
            "address": "北京市亦庄经济开发区",
        },
        {
            "code": "KH-MT",
            "name": "美团点评",
            "short_name": "美团",
            "level": "normal",
            "contact": "孙总监",
            "phone": "13800001006",
            "email": "sun@meituan.com",
            "region": "华北",
            "industry": "本地生活",
            "address": "北京市朝阳区望京东路",
        },
        {
            "code": "KH-XM",
            "name": "小米科技",
            "short_name": "小米",
            "level": "normal",
            "contact": "周经理",
            "phone": "13800001007",
            "email": "zhou@xiaomi.com",
            "region": "华北",
            "industry": "消费电子",
            "address": "北京市海淀区清河中街",
        },
        {
            "code": "KH-WY",
            "name": "网易公司",
            "short_name": "网易",
            "level": "normal",
            "contact": "吴主管",
            "phone": "13800001008",
            "email": "wu@netease.com",
            "region": "华东",
            "industry": "互联网",
            "address": "杭州市滨江区网商路",
        },
        {
            "code": "KH-PDD",
            "name": "拼多多",
            "short_name": "拼多多",
            "level": "normal",
            "contact": "郑经理",
            "phone": "13800001009",
            "email": "zheng@pdd.com",
            "region": "华东",
            "industry": "电商",
            "address": "上海市长宁区娄山关路",
        },
        {
            "code": "KH-CT",
            "name": "携程旅行",
            "short_name": "携程",
            "level": "normal",
            "contact": "冯总监",
            "phone": "13800001010",
            "email": "feng@ctrip.com",
            "region": "华东",
            "industry": "旅游",
            "address": "上海市长宁区金钟路",
        },
        {
            "code": "KH-DD",
            "name": "滴滴出行",
            "short_name": "滴滴",
            "level": "potential",
            "contact": "陈经理",
            "phone": "13800001011",
            "email": "chen@didi.com",
            "region": "华北",
            "industry": "出行",
            "address": "北京市海淀区中关村软件园",
        },
        {
            "code": "KH-ZMJF",
            "name": "蚂蚁金服",
            "short_name": "蚂蚁",
            "level": "potential",
            "contact": "林主管",
            "phone": "13800001012",
            "email": "lin@antfin.com",
            "region": "华东",
            "industry": "金融科技",
            "address": "杭州市西湖区万塘路",
        },
        {
            "code": "KH-BYD",
            "name": "比亚迪股份",
            "short_name": "比亚迪",
            "level": "potential",
            "contact": "何经理",
            "phone": "13800001013",
            "email": "he@byd.com",
            "region": "华南",
            "industry": "汽车",
            "address": "深圳市坪山区比亚迪路",
        },
        {
            "code": "KH-ZTE",
            "name": "中兴通讯",
            "short_name": "中兴",
            "level": "potential",
            "contact": "罗总监",
            "phone": "13800001014",
            "email": "luo@zte.com",
            "region": "华南",
            "industry": "通信",
            "address": "深圳市南山区高新技术产业园",
        },
        {
            "code": "KH-DJ",
            "name": "大疆创新",
            "short_name": "大疆",
            "level": "potential",
            "contact": "谢经理",
            "phone": "13800001015",
            "email": "xie@dji.com",
            "region": "华南",
            "industry": "无人机",
            "address": "深圳市南山区高新南四道",
        },
    ]

    customers = []
    for spec in customer_specs:
        customer, _ = Customer.objects.get_or_create(
            code=spec["code"],
            defaults={
                "name": spec["name"],
                "short_name": spec["short_name"],
                "level": spec["level"],
                "contact_person": spec["contact"],
                "contact_phone": spec["phone"],
                "contact_email": spec["email"],
                "region": spec["region"],
                "industry": spec["industry"],
                "address": spec["address"],
                "is_active": True,
            },
        )
        customers.append(customer)

    print(f"  Created {len(customers)} customers")
    return customers


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


def create_operation_logs(users):
    print("Creating operation logs...")
    OperationLog.objects.all().delete()
    now = timezone.now()
    admin = users[0]
    operator = users[1] if len(users) > 1 else admin
    viewer = users[2] if len(users) > 2 else operator

    log_data = [
        {
            "user": admin,
            "action": "LOGIN",
            "category": "security",
            "level": "info",
            "target": "/api/v1/auth/login/",
            "detail": "用户登录系统",
            "method": "POST",
            "path": "/api/v1/auth/login/",
            "status_code": 200,
            "ip_address": "192.168.1.100",
            "duration_ms": 156,
            "module": "auth",
            "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            "created_at": now - timedelta(hours=12),
        },
        {
            "user": operator,
            "action": "LOGIN",
            "category": "security",
            "level": "info",
            "target": "/api/v1/auth/login/",
            "detail": "用户登录系统",
            "method": "POST",
            "path": "/api/v1/auth/login/",
            "status_code": 200,
            "ip_address": "192.168.1.101",
            "duration_ms": 89,
            "module": "auth",
            "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "created_at": now - timedelta(hours=11),
        },
        {
            "user": None,
            "action": "LOGIN_FAILED",
            "category": "security",
            "level": "warning",
            "target": "/api/v1/auth/login/",
            "detail": "用户登录失败",
            "method": "POST",
            "path": "/api/v1/auth/login/",
            "status_code": 401,
            "ip_address": "10.0.0.55",
            "duration_ms": 45,
            "module": "auth",
            "user_agent": "python-requests/2.28.0",
            "created_at": now - timedelta(hours=10),
        },
        {
            "user": admin,
            "action": "CREATE",
            "category": "operation",
            "level": "info",
            "target": "/api/v1/contracts/",
            "detail": "POST /api/v1/contracts/",
            "method": "POST",
            "path": "/api/v1/contracts/",
            "status_code": 201,
            "ip_address": "192.168.1.100",
            "duration_ms": 234,
            "module": "contracts",
            "after_data": {
                "title": "2024年度IT服务合同",
                "client_name": "华为技术有限公司",
                "amount": 500000,
            },
            "created_at": now - timedelta(hours=9),
        },
        {
            "user": operator,
            "action": "UPDATE",
            "category": "operation",
            "level": "info",
            "target": "/api/v1/contracts/1/",
            "detail": "PATCH /api/v1/contracts/1/",
            "method": "PATCH",
            "path": "/api/v1/contracts/1/",
            "status_code": 200,
            "ip_address": "192.168.1.101",
            "duration_ms": 178,
            "module": "contracts",
            "before_data": {"status": "draft"},
            "after_data": {"status": "active"},
            "created_at": now - timedelta(hours=8),
        },
        {
            "user": admin,
            "action": "DELETE",
            "category": "operation",
            "level": "warning",
            "target": "/api/v1/contracts/5/",
            "detail": "DELETE /api/v1/contracts/5/",
            "method": "DELETE",
            "path": "/api/v1/contracts/5/",
            "status_code": 204,
            "ip_address": "192.168.1.100",
            "duration_ms": 67,
            "module": "contracts",
            "before_data": {"id": 5, "title": "已废弃合同"},
            "created_at": now - timedelta(hours=7),
        },
        {
            "user": admin,
            "action": "ALERT_SCAN",
            "category": "system",
            "level": "info",
            "target": "alerts:scan",
            "detail": "执行预警扫描，新增 3 条消息",
            "method": "POST",
            "path": "/api/v1/system/alerts/scan/",
            "status_code": 200,
            "ip_address": "192.168.1.100",
            "duration_ms": 1520,
            "module": "system",
            "after_data": {"created_count": 3},
            "created_at": now - timedelta(hours=6),
        },
        {
            "user": admin,
            "action": "ALERT_PROCESS",
            "category": "system",
            "level": "info",
            "target": "alert:1",
            "detail": "处理预警《付款预警 - CT-2024-001》",
            "method": "POST",
            "path": "/api/v1/system/alert-workspace/1/process/",
            "status_code": 200,
            "ip_address": "192.168.1.100",
            "duration_ms": 89,
            "module": "system",
            "before_data": {"status": "pending"},
            "after_data": {"status": "processed"},
            "created_at": now - timedelta(hours=5),
        },
        {
            "user": admin,
            "action": "ALERT_REASSIGN",
            "category": "system",
            "level": "info",
            "target": "alert:2",
            "detail": "将预警《交付预警 - CT-2024-002》改派给 operator1",
            "method": "POST",
            "path": "/api/v1/system/alert-workspace/2/reassign/",
            "status_code": 200,
            "ip_address": "192.168.1.100",
            "duration_ms": 112,
            "module": "system",
            "before_data": {"owner_name": "admin"},
            "after_data": {"owner_name": "operator1"},
            "created_at": now - timedelta(hours=4),
        },
        {
            "user": operator,
            "action": "VIEW",
            "category": "operation",
            "level": "info",
            "target": "/api/v1/system/logs/",
            "detail": "查看 /api/v1/system/logs/",
            "method": "GET",
            "path": "/api/v1/system/logs/",
            "status_code": 200,
            "ip_address": "192.168.1.101",
            "duration_ms": 45,
            "module": "system",
            "created_at": now - timedelta(hours=3),
        },
        {
            "user": admin,
            "action": "UPDATE",
            "category": "operation",
            "level": "info",
            "target": "/api/v1/system/alert-rules/1/",
            "detail": "PATCH /api/v1/system/alert-rules/1/",
            "method": "PATCH",
            "path": "/api/v1/system/alert-rules/1/",
            "status_code": 200,
            "ip_address": "192.168.1.100",
            "duration_ms": 98,
            "module": "system",
            "before_data": {"remind_days": 7},
            "after_data": {"remind_days": 14},
            "created_at": now - timedelta(hours=2),
        },
        {
            "user": None,
            "action": "CREATE",
            "category": "error",
            "level": "error",
            "target": "/api/v1/contracts/",
            "detail": "POST /api/v1/contracts/",
            "method": "POST",
            "path": "/api/v1/contracts/",
            "status_code": 500,
            "ip_address": "192.168.1.200",
            "duration_ms": 5230,
            "module": "contracts",
            "after_data": {"error": "Internal Server Error"},
            "created_at": now - timedelta(hours=1, minutes=30),
        },
        {
            "user": operator,
            "action": "UPDATE",
            "category": "error",
            "level": "error",
            "target": "/api/v1/contracts/3/",
            "detail": "PATCH /api/v1/contracts/3/",
            "method": "PATCH",
            "path": "/api/v1/contracts/3/",
            "status_code": 400,
            "ip_address": "192.168.1.101",
            "duration_ms": 34,
            "module": "contracts",
            "after_data": {"error": "Invalid data"},
            "created_at": now - timedelta(hours=1),
        },
        {
            "user": admin,
            "action": "CREATE",
            "category": "operation",
            "level": "info",
            "target": "/api/v1/system/data-permissions/",
            "detail": "POST /api/v1/system/data-permissions/",
            "method": "POST",
            "path": "/api/v1/system/data-permissions/",
            "status_code": 201,
            "ip_address": "192.168.1.100",
            "duration_ms": 67,
            "module": "system",
            "after_data": {"user": 2, "scope_type": "department"},
            "created_at": now - timedelta(minutes=45),
        },
        {
            "user": admin,
            "action": "LOGOUT",
            "category": "security",
            "level": "info",
            "target": "/api/v1/auth/logout/",
            "detail": "用户退出系统",
            "method": "POST",
            "path": "/api/v1/auth/logout/",
            "status_code": 200,
            "ip_address": "192.168.1.100",
            "duration_ms": 23,
            "module": "auth",
            "created_at": now - timedelta(minutes=30),
        },
        {
            "user": admin,
            "action": "VIEW",
            "category": "operation",
            "level": "info",
            "target": "/api/v1/system/backup/",
            "detail": "查看 /api/v1/system/backup/",
            "method": "GET",
            "path": "/api/v1/system/backup/",
            "status_code": 200,
            "ip_address": "192.168.1.100",
            "duration_ms": 312,
            "module": "system",
            "created_at": now - timedelta(minutes=15),
        },
        {
            "user": None,
            "action": "LOGIN_FAILED",
            "category": "security",
            "level": "critical",
            "target": "/api/v1/auth/login/",
            "detail": "用户登录失败",
            "method": "POST",
            "path": "/api/v1/auth/login/",
            "status_code": 401,
            "ip_address": "203.0.113.50",
            "duration_ms": 12,
            "module": "auth",
            "user_agent": "curl/7.88.1",
            "created_at": now - timedelta(minutes=5),
        },
        {
            "user": admin,
            "action": "UPDATE",
            "category": "operation",
            "level": "warning",
            "target": "/api/v1/system/integrations/1/",
            "detail": "PUT /api/v1/system/integrations/1/",
            "method": "PUT",
            "path": "/api/v1/system/integrations/1/",
            "status_code": 200,
            "ip_address": "192.168.1.100",
            "duration_ms": 4500,
            "module": "system",
            "before_data": {"sync_interval": 60},
            "after_data": {"sync_interval": 30},
            "created_at": now - timedelta(minutes=2),
        },
    ]

    logs = [OperationLog(**data) for data in log_data]
    OperationLog.objects.bulk_create(logs)
    print(f"  Created {len(logs)} operation logs")


def main():
    print("=== Inserting test data...")
    users = create_users()
    create_departments(users)
    create_product_types()
    create_customers()
    contracts = create_contracts(users)
    create_contract_related_data(contracts, users)
    create_governance_data(users, contracts)
    create_operation_logs(users)
    print("=== Done!")


if __name__ == "__main__":
    main()
