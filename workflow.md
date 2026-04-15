# Workflow

## 2026-04-15 预警中心闭环迭代

- 目标：补齐登录后头部消息中心，让预警从治理后台下沉到全局入口，形成可查看、可处理、可验证的闭环。
- 后端：新增当前登录用户可访问的预警中心汇总接口与处理接口，按角色过滤消息范围并输出待处理数量、等级统计、最近预警列表。
- 前端：将 `AppHeader.vue` 的静态铃铛替换为真实预警弹层，展示未处理数量、风险等级、合同编号、截止时间，并支持就地处理。
- 数据：增强 `insert_test_data.py` 的预警样例，生成多等级、多状态、多负责人消息，便于本地联调与演示。
- 验证：`frontend` 已执行 `npm run build` 并通过；IDE 诊断未发现新增语法问题；`backend` 执行 `python3 manage.py check --settings=contract_vision.settings.development` 时因本机未安装 Django 依赖而中断，待补齐虚拟环境后继续验证。

## 2026-04-15 预警工作台迭代

- 目标：把预警能力从头部入口扩展为独立业务工作台，支持分页检索、时效分类、批量处理与合同明细跳转。
- 后端：新增 `alert-workspace` 只读/处理接口，支持按状态、等级、类型、关键词、合同编号、截止范围筛选，并新增汇总统计与批量处理动作。
- 基础能力：增强 `StandardPagination`，同时兼容 `size` 与 `page_size` 两种分页参数，降低前后端历史接口不一致带来的联调成本。
- 前端：新增 `frontend/src/views/contract/alerts.vue` 页面，并在路由、侧边栏、头部预警入口中接入该页面，形成统一的预警主导航。
- 验证：`frontend` 再次执行 `npm run build` 并通过；新增页面与相关文件的 IDE 诊断通过；后端仍待安装 Django 依赖后执行运行时校验。

## 2026-04-15 预警详情与重分派迭代

- 目标：将预警工作台从“列表处理”升级为“可追踪、可重分派、可精确归属”的处置中心，补齐详情抽屉和管理员调度能力。
- 后端：重构预警扫描归属策略，按付款、交付、续签、目标四类分别解析负责人；为 `alert-workspace` 增加详情查询、负责人候选列表与管理员重分派动作。
- 前端：重做 `frontend/src/views/contract/alerts.vue`，新增详情侧滑抽屉、处置建议区、负责人筛选、管理员远程搜索分派和处理后即时刷新联动。
- 数据：更新 `backend/insert_test_data.py`，让合同创建人/续签负责人固定落到业务角色，并新增更符合规则归属的目标预警样例，保证本地演示不出现“负责人缺失”。
- 验证：`frontend` 已执行 `npm run build` 并通过；`backend/apps/system/config_views.py` 与 `backend/insert_test_data.py` 已通过 `python3 -m py_compile` 语法校验；前端改动文件 IDE 诊断无新增错误；后端运行时校验仍受本机 Django 依赖缺失影响，需补齐环境后继续 `manage.py check`。

## 2026-04-15 预警扫描摘要与审计追踪迭代

- 目标：把预警能力从“可扫描、可处理”继续升级为“可验证、可回溯、可复盘”，让治理后台能直接看到扫描结果、最近处置与合同快照。
- 后端：为 `alerts/scan/` 输出新增分类统计与最近命中摘要，新增 `alerts/scan_summary/` 汇总接口；在预警处理与重分派时写入精细化操作日志，并在 `alert-workspace` 详情接口中追加 `contract_snapshot` 与 `recent_logs`。
- 前端：重构 `frontend/src/views/system/governance.vue`，新增扫描摘要卡片、最近扫描历史、最近处置审计面板与工作台快捷入口；增强 `frontend/src/views/contract/alerts.vue` 抽屉，直接展示合同快照和最近操作轨迹。
- 验证：`backend/apps/system/config_views.py` 已通过 `python3 -m py_compile`；`frontend` 已再次执行 `npm run build` 并通过；`frontend/src/views/system/governance.vue`、`frontend/src/views/contract/alerts.vue`、`frontend/src/api/system.js` IDE 诊断无新增错误；后端运行时检查仍待 Django 依赖补齐后执行。

## 2026-04-15 预警扫描试运行预览迭代

- 目标：在正式执行预警扫描前，先向管理员展示“本次将命中哪些预警、将归属给谁、哪些会被重复拦截”，降低规则调整与演练成本。
- 后端：抽离预警命中预览生成逻辑，为 `alerts/scan_preview/` 输出命中总数、可新建总数、分类统计、负责人归属和重复待处理拦截标记；正式扫描复用同一套规则生成结果，确保预览与落库一致。
- 前端：增强 `frontend/src/views/system/governance.vue`，新增扫描试运行预览面板，展示预警标题、合同编号、负责人归属、是否已存在待处理消息与可新建数量。
- 验证：`backend/apps/system/config_views.py` 已通过 `python3 -m py_compile`；`frontend` 已再次执行 `npm run build` 并通过；`frontend/src/views/system/governance.vue` 与 `frontend/src/api/system.js` IDE 诊断无新增错误；后端运行时校验仍待 Django 依赖安装后执行。

## 2026-04-15 规则级试运行与审计筛选迭代

- 目标：让治理台从“能看结果”升级为“能定向分析”，支持只预览某一类规则命中，并对最近处置按预警类型、动作、操作人和时间范围精准过滤。
- 后端：增强 `alerts/scan_preview/`，支持 `rule_type` 与 `only_creatable` 参数；增强 `alerts/scan_summary/`，支持按 `warning_type`、`action`、`operator`、`date_from`、`date_to` 过滤审计轨迹与统计结果。
- 前端：增强 `frontend/src/views/system/governance.vue`，新增规则级预览筛选、仅看将新建开关、审计过滤器和重置操作，形成真正可操作的治理分析台。
- 验证：`backend/apps/system/config_views.py` 已通过 `python3 -m py_compile`；`frontend` 已再次执行 `npm run build` 并通过；`frontend/src/views/system/governance.vue` 与 `frontend/src/api/system.js` IDE 诊断无新增错误；后端运行时校验仍待 Django 依赖安装后执行。

## 2026-04-15 负责人策略可视化与来源解释迭代

- 目标：让管理员和业务侧都能直接理解“为什么这条预警会命中、为什么会分配给当前负责人”，并支持将试运行结果导出做线下复盘。
- 后端：在预警预览与详情中新增 `owner_strategy`、`trigger_summary` 字段；为扫描预览与扫描摘要统一返回负责人策略目录；新增 `scan_preview_export` 导出接口输出 CSV 结果。
- 前端：增强 `frontend/src/views/system/governance.vue`，新增负责人策略面板、试运行结果中的策略说明/命中说明列和导出预览能力；增强 `frontend/src/views/contract/alerts.vue` 抽屉，新增“来源解释”区块展示归属原因与触发原因。
- 验证：`backend/apps/system/config_views.py` 已通过 `python3 -m py_compile`；`frontend` 已再次执行 `npm run build` 并通过；`frontend/src/views/system/governance.vue`、`frontend/src/views/contract/alerts.vue`、`frontend/src/api/system.js` IDE 诊断无新增错误；后端运行时校验仍待 Django 依赖安装后执行。

## 2026-04-15 命中链路时间轴与审计导出迭代

- 目标：把预警详情进一步升级为“可回放链路”的工作台视图，并让治理台可按当前筛选条件导出处置审计，支持复盘留痕。
- 后端：增强 `alert-workspace` 详情数据，在返回中追加 `timeline` 时间轴，串联预警生成、负责人匹配、截止节点、管理员操作与最终处理结果；增强扫描摘要返回的最近处置记录，补充预警类型字段用于导出与展示。
- 前端：增强 `frontend/src/views/contract/alerts.vue` 抽屉，新增“命中链路时间轴”区块；增强 `frontend/src/views/system/governance.vue`，新增按当前筛选结果导出处置审计 CSV 的能力。
- 验证：`backend/apps/system/config_views.py` 已通过 `python3 -m py_compile`；`frontend` 已再次执行 `npm run build` 并通过；`frontend/src/views/system/governance.vue` 与 `frontend/src/views/contract/alerts.vue` IDE 诊断无新增错误；后端运行时校验仍待 Django 依赖安装后执行。

## 2026-04-15 负责人策略配置化迭代

- 目标：将预警负责人归属从硬编码规则升级为后台可配置策略，让管理员可以直接在治理台维护不同预警类型的归属口径，并让试运行结果同步反映配置变化。
- 后端：复用 `AlertRule.owner_role` 作为负责人策略键，扩展付款、交付、到期、发票、目标五类预警的可选策略目录；重构扫描预览、正式扫描、详情解释中的负责人解析逻辑，使其按规则配置动态匹配；新增 `alert-rules/strategy_options/` 接口，向前端返回策略选项、默认值和当前配置目录。
- 前端：增强 `frontend/src/views/system/governance.vue`，新增预警规则编辑能力、策略下拉选择、策略说明文案和当前/推荐配置展示；预览表中的“策略说明”列改为展示实际生效的配置策略。
- 数据：更新 `backend/insert_test_data.py` 中的预警规则初始化数据，为不同预警类型写入更准确的默认负责人策略，减少本地演示时的旧值歧义。
- 验证：`backend` 已执行 `python3 -m py_compile apps/system/config_views.py insert_test_data.py` 并通过；`frontend` 已执行 `npm run build` 并通过；`frontend/src/views/system/governance.vue`、`frontend/src/api/system.js`、`backend/insert_test_data.py` IDE 诊断无新增错误；后端运行时检查仍待 Django 依赖补齐后继续执行。

## 2026-04-15 策略变更影响预览迭代

- 目标：让管理员在保存预警负责人策略前，先看到“哪些命中项会改派给谁”，降低规则调整带来的不可见风险。
- 后端：增强 `collect_alert_scan_preview` 支持负责人策略覆盖模拟；新增 `alert-rules/preview_impact/` 接口，对比当前策略与拟改策略下的负责人差异，返回变更条数、保持不变条数与样例清单。
- 前端：增强 `frontend/src/views/system/governance.vue` 规则编辑弹窗，新增“预览改派影响”操作、差异汇总卡片与命中清单，展示当前负责人和拟改后负责人对比。
- 验证：`backend` 已执行 `python3 -m py_compile apps/system/config_views.py` 并通过；`frontend` 已执行 `npm run build` 并通过；`frontend/src/views/system/governance.vue` 与 `frontend/src/api/system.js` IDE 诊断无新增错误；后端仍仅保留既有未使用参数提示。
