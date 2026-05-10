# 基于Python的企业销售合同数据可视化平台

本项目为工程实践类毕业设计项目，面向企业销售管理数字化转型需求，基于Python生态构建一站式销售合同数据可视化分析平台。项目旨在解决传统企业销售合同数据分散存储、分析手段单一、可视化程度低、数据价值挖掘不足等核心痛点，实现合同数据全生命周期管理、多维度统计分析、交互式可视化展示、自定义报表生成与分级权限管控，将复杂的业务数据转化为直观的决策指标，助力企业提升经营决策的科学性与时效性，推动销售管理向数据驱动型转型。

## 开源说明

- 开源协议：MIT，详见 `LICENSE`
- 敏感配置：仓库不包含真实数据库密码、密钥等敏感信息
- 本地启动前请先复制 `backend/.env.example` 为 `backend/.env`，再按实际环境填写数据库和 Redis 配置

## 快速启动

### 后端

```bash
cd backend
cp .env.example .env
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

### 前端

```bash
cd frontend
npm install
npm run dev
```

## 角色与权限系统

平台采用精细化分级权限设计，基于业务场景划分三类核心角色，明确不同角色的操作边界与数据访问范围，兼顾系统安全性与使用便捷性。

| 角色名称     | 核心权限范围                                                                                                     | 核心业务职责                                                       |
| ------------ | ---------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------ |
| 系统管理员   | 系统全功能操作权限，包含用户全生命周期管理、合同数据全局管控、系统配置、深度数据分析、权限分配、数据备份与恢复等 | 系统运维、用户体系管理、数据标准化管控、系统安全保障、业务配置管理 |
| 普通操作员   | 账号自主管理、合同数据增删改查、多维度可视化查看、自定义报表生成与导出、基础数据统计分析                         | 合同数据日常维护、业务数据分析、报表制作与业务汇报                 |
| 只读查看用户 | 账号基础信息管理、合同数据多条件查询、可视化图表查看、报表查看与导出，无数据编辑与系统配置权限                   | 业务经营状况监控、数据查看与决策参考                               |

## 核心技术选型

本项目技术选型均基于Python生态及主流前后端开发框架，兼顾技术成熟度、开源性与可扩展性，与项目需求高度匹配。

### 后端技术栈

- 核心开发语言：Python 3.x
- Web服务框架：Django
- 数据处理库：Pandas、NumPy
- 智能分析库：Scikit-learn
- 接口规范：RESTful API

### 前端技术栈

- 基础页面技术：HTML5、CSS3、JavaScript (ES6+)
- 前端框架：Vue.js
- UI组件库：Element UI
- 可视化图表库：ECharts、Highcharts

### 数据库与缓存

- 关系型数据库：MySQL 8.0+（存储用户信息、合同业务数据、系统配置数据）
- 缓存数据库：Redis（高频数据缓存，提升海量数据查询与加载效率）

### 开发与运行环境

- 核心开发工具：PyCharm
- 环境管理工具：Anaconda
- 运行环境支持：Windows、Linux 主流操作系统
- 部署模式：支持本地部署与企业服务器私有化部署

## 核心功能模块

### 1. 用户认证与权限管理模块

平台核心基础模块，实现多角色用户的全生命周期管理，涵盖用户注册、安全登录、密码找回、角色权限分配、账号状态管控、操作日志记录等功能，通过分级权限设计保障系统数据安全与操作合规性。

### 2. 销售合同数据管理模块

平台核心数据底座模块，实现销售合同全维度数据的标准化管理，支持合同数据的批量导入/导出、单条增删改查、数据清洗去重、格式标准化校验、数据自动备份等功能，保障合同数据的准确性、完整性与实时性。数据覆盖合同基本信息、成交金额、客户信息、产品信息、交付周期、签约区域等全业务字段。

### 3. 多维度数据可视化分析模块

平台核心能力模块，基于标准化合同数据，支持按时间（年/季/月/周）、产品、区域、客户等维度进行统计分析，动态生成折线图、柱状图、饼图、热力图、雷达图等多样化交互式可视化图表，直观呈现销售业绩趋势、产品销售占比、区域业绩分布、客户价值贡献等核心指标，支持图表放大、缩小、钻取、导出等交互操作。

### 4. 自定义报表生成模块

面向企业办公场景的核心模块，支持用户按需选择数据维度、统计指标与时间范围，自动生成标准化业务报表，包含月度销售合同汇总表、客户业绩贡献表、产品销售分析表、区域业绩统计表等，支持Excel、PDF等多格式报表导出，满足企业日常办公、业务汇报、经营复盘的全场景需求。

### 5. 系统管理与智能分析模块

面向管理员的系统运维与高阶分析模块，支持可视化图表模板自定义、数据统计维度配置、系统接口管理、CRM/ERP等第三方系统对接配置、数据备份策略设置等系统管理功能；同时基于机器学习算法实现销售趋势预测、异常合同识别、客户信用评级等智能化分析，为企业管理层提供高阶决策支持。

## 功能详细需求表

| 编号 | 功能名称 | 前端入口 | 后端接口（/api） | 适用角色 | 已实现范围（关键点） |
| ---- | -------- | -------- | ---------------- | -------- | -------------------- |
| F001 | 用户账号注册 | /register | POST /v1/auth/register/ | 全角色（未登录） | 支持 username/email/phone/company_name/department/region 注册；密码强度校验（8位+大小写+数字），不包含验证码/短信校验；默认角色为 viewer |
| F002 | 用户登录认证 | /login | POST /v1/auth/login/; POST /v1/auth/token/refresh/ | 全角色（未登录） | 使用 JWT 登录，返回 access/refresh/user；不包含验证码/双因子 |
| F003 | 密码找回 | /forgot-password | POST /v1/auth/password-reset/ | 全角色（未登录） | 通过 username + phone 校验身份并重置密码，不包含短信/邮箱验证码 |
| F004 | 个人资料与改密 | /profile | GET/PUT /v1/users/profile/; POST /v1/auth/change-password/ | 全角色 | 支持更新邮箱/手机号/公司/部门/区域等；改密需校验旧密码 |
| F005 | 用户账号查询 | /system/user | GET /v1/users/manage/; GET /v1/users/manage/:id/ | 系统管理员 | 用户列表分页、关键字搜索、详情查询 |
| F006 | 用户启用/禁用 | /system/user | POST /v1/users/manage/:id/toggle_active/; DELETE /v1/users/manage/:id/ | 系统管理员 | 支持启用/禁用账号；禁用账号将无法通过登录校验 |
| F007 | 用户角色分配 | /system/user | POST /v1/users/manage/:id/assign_role/ | 系统管理员 | 支持将用户角色切换为 admin/operator/viewer |
| F008 | 合同数据单条录入/编辑/详情 | /contract/create, /contract/edit/:id, /contract/detail/:id | GET/POST /v1/contracts/; GET/PUT/PATCH/DELETE /v1/contracts/:id/ | 系统管理员、普通操作员（写）；查看者（读） | 合同 CRUD；写操作受角色限制；终止/作废合同禁止编辑 |
| F009 | 合同批量导入与模板 | /contract/list | POST /v1/contracts/batch_import/; GET /v1/contracts/import_template/ | 系统管理员、普通操作员 | 支持 CSV/XLSX 导入；校验必要列、合同编号重复、金额>0；导入模板可下载 |
| F010 | 合同多条件检索与分页 | /contract/list | GET /v1/contracts/ | 全角色 | 支持多字段筛选/搜索/排序；分页参数兼容 size 与 page_size |
| F011 | 合同修改审批链路 | /system/governance | PUT/PATCH /v1/contracts/:id/; /v1/contracts/approval-processes/; /v1/contracts/approval-requests/ | 系统管理员、普通操作员（提交）；系统管理员（审批） | 根据审批流程配置，合同新增/修改/删除可进入待审批并由管理员通过/驳回后生效 |
| F012 | 合同删除（软删除/批量软删） | /contract/list | DELETE /v1/contracts/:id/; POST /v1/contracts/batch_delete/ | 系统管理员、普通操作员 | 采用软删除（is_deleted）；支持批量软删；不提供硬删除/恢复的对外接口 |
| F013 | 合同导出（Excel/PDF） | /contract/list | GET /v1/contracts/export/; GET /v1/contracts/export_pdf/ | 全角色 | 支持导出筛选结果为 Excel 与 PDF |
| F014 | 首页概览指标 | /dashboard, /analytics/overview | GET /v1/analytics/dashboard/; GET /v1/analytics/overview-summary/ | 全角色 | 合同总量/金额、本月新增、逾期合同等指标汇总展示 |
| F015 | 多维可视化分析 | /analytics/trend, /analytics/region, /analytics/overview | GET /v1/analytics/trend/ /region/ /product/ /status/ /top-clients/ /salesperson-ranking/ /department-ranking/ /monthly-trend/ | 全角色 | 基于合同数据生成趋势/区域/产品/状态分布及排名等图表（ECharts 渲染） |
| F016 | 自定义报表生成 | /analytics/report | POST /v1/analytics/report/generate/ | 系统管理员、普通操作员 | 支持月度汇总/客户/产品/区域/销售等报表生成（返回 columns/rows） |
| F017 | 报表导出（Excel/PDF） | /analytics/report | POST /v1/analytics/report/export/ | 全角色 | 将已生成报表导出为 Excel 或 PDF |
| F018 | 数据备份与恢复 | /system/backup | GET /v1/system/backup/; POST /v1/system/backup/create/; POST /v1/system/backup/restore/; POST /v1/system/backup/delete/ | 系统管理员 | 基于 mysqldump/mysql 的手动备份、恢复与备份文件管理 |
| F019 | 智能分析（预测/异常/客户价值） | /analytics/prediction | POST /v1/analytics/prediction/; GET /v1/analytics/anomaly-detection/; GET /v1/analytics/customer-value/ | 系统管理员 | 线性回归销售预测（依赖 scikit-learn，未安装会返回提示）；金额异常检测；客户价值分层 |
| F020 | 第三方系统集成配置 | /system/integration | /v1/system/integrations/; POST /v1/system/integrations/:id/test_connection/; POST /v1/system/integrations/:id/toggle_status/ | 系统管理员 | 集成配置 CRUD；支持连通性测试与启停 |
| F021 | 合同履约进度跟踪 | /contract/lifecycle | /v1/contracts/milestones/; GET /v1/contracts/:id/fulfillment/ | 系统管理员、普通操作员（写）；查看者（读） | 支持交付/付款/验收等里程碑维护；自动计算履约完成率与风险节点数 |
| F022 | 付款计划与逾期/开票管理 | /contract/lifecycle | /v1/contracts/payment-plans/; POST /v1/contracts/payment-plans/:id/mark_paid/; GET /v1/contracts/payment-plans/overview/ | 系统管理员、普通操作员（写）；查看者（读） | 分期回款计划维护；开票状态字段；逾期统计（含严重逾期计数） |
| F023 | 合同到期与续签管理 | /contract/lifecycle | GET /v1/contracts/renewal_summary/; POST /v1/contracts/:id/renew/ | 系统管理员、普通操作员 | 支持临期/到期统计与列表；续签状态登记与续签合同编号关联（预警扫描为手动触发） |
| F024 | 合同变更与补充协议 | /contract/lifecycle | /v1/contracts/change-requests/; POST /v1/contracts/change-requests/:id/approve/; POST /v1/contracts/change-requests/:id/reject/ | 系统管理员、普通操作员 | 变更申请留存前后快照；支持审批通过/驳回 |
| F025 | 合同终止与作废 | /contract/lifecycle | POST /v1/contracts/:id/terminate/ | 系统管理员、普通操作员 | 支持终止/作废及原因/生效日期记录；终止/作废后禁止编辑 |
| F026 | 审批流程配置与处置 | /system/governance | /v1/contracts/approval-processes/; /v1/contracts/approval-requests/ (approve/reject) | 系统管理员 | 支持新增/修改/删除/变更的审批流程配置与审批处理 |
| F027 | 行级数据权限管控 | /system/governance | /v1/system/data-permissions/ | 系统管理员 | 按本人/部门/区域/客户/全部配置数据范围，合同列表与统计分析按规则过滤 |
| F028 | 操作审计与导出 | /system/log | /v1/system/logs/; GET /v1/system/logs/export/ | 系统管理员 | 中间件记录非 GET 请求操作日志（方法/路径/状态码/IP/请求体快照）；预警处置链路写入更细粒度审计项 |
| F029 | 数据质量校验与评分 | /contract/lifecycle | GET /v1/contracts/quality-report/; POST /v1/contracts/:id/recalculate_quality/ | 系统管理员、普通操作员 | 基于缺失字段/日期逻辑/金额/汇率换算等规则打分并给出整改建议 |
| F030 | 重复合同识别与合并 | /contract/lifecycle | GET/POST /v1/contracts/duplicate-scan/ | 系统管理员 | 基于编号/客户/标题相似度与金额差异分组，支持选择主合同合并去重 |
| F031 | 合同预警闭环（规则/试运行/工作台/审计） | /contract/alerts, /system/governance, header bell | /v1/system/alert-rules/ (strategy_options/preview_impact); /v1/system/alerts/ (scan/scan_preview/scan_summary/scan_preview_export); /v1/system/alert-center/; /v1/system/alert-workspace/ (summary/assignees/process/batch_process/reassign) | 全角色（查看/处理）；管理员（配置/扫描/重分派） | 支持试运行预览与 CSV 导出、规则级筛选、负责人策略解释、详情抽屉（合同快照/来源解释/时间轴）、就地处理与管理员重分派；处置动作写入审计日志 |

| F037 | 数据模板库（导入/导出/报表） | /system/config-center | /v1/system/templates/ | 系统管理员 | 模板字段配置与版本管理（用于治理与扩展对接，导入/导出接口当前仍使用内置字段集） |
| F038 | 多币种汇率与本位币换算 | /system/config-center | /v1/system/currency-rates/ | 系统管理员 | 维护汇率；合同指标计算时按签约日 sign_date 汇率换算 base_amount |
| F039 | 移动端驾驶舱 | /dashboard/mobile | GET /v1/system/mobile-dashboard/ | 全角色 | 移动端汇总合同总数/金额、待处理预警、30 天内到期等指标，并返回移动端模板配置 |
