# FAC × M13 财务智能体登记规范 V1.0

## 1. 原则

M09负责财务业务与智能体使用，M13负责智能体注册、版本、Skill绑定、生命周期和运行状态。
任何未在M13登记、未授权或状态非“已发布”的财务智能体，不得被FAC正式调用。

## 2. 最小登记字段

- agent_id
- 中文名称
- 所属系统：M09 FAC
- 注册中心：M13
- 专业领域
- owner
- skill_ids
- data_scope
- operation_scope
- autonomy_level
- guard_policy
- evidence_policy
- version
- status
- effective_at
- audit_ref

## 3. 首批登记清单

- AG-FAC-001 财务总监智能体
- AG-FAC-002 收入智能体
- AG-FAC-003 成本智能体
- AG-FAC-004 毛利智能体
- AG-FAC-005 应收智能体
- AG-FAC-006 资金智能体
- AG-FAC-007 预算智能体
- AG-FAC-008 ROI智能体
- AG-FAC-009 财务风险与机会智能体
- AG-FAC-010 财经复盘智能体

## 4. 生命周期

草稿 → 测试 → 评审 → 已发布 → 运行监控 → 升级/降级 → 停用

## 5. 权限规则

- A0：读取/解释
- A1：分析/建议/生成DecisionCase
- A2：低风险自动重算、提醒、报告
- A3：仅白名单、受Guard限制
- 高风险付款、调账、重大预算变更、最终价值Verify必须保留人工责任

## 6. Agent与Skill边界

Agent = 被登记、授权、监控的执行主体。  
Skill = Agent可调用的专业能力。  
正式财务数字必须由Skill/规则/正式数据对象产生，Agent不得自行编造正式财务数值。

## 7. FAC展示要求

FAC只展示：
- M13登记号
- 当前版本
- Skill数量
- 自治等级
- Owner
- 运行状态
- 最近调用
- 异常/审计摘要

完整注册详情、版本和生命周期管理跳转M13。
