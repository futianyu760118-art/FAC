# FAC Finance Skill 标准规范 V1.0

## 1. 定义

Finance Skill不是Prompt，而是可测试、可版本、可审计、可验证的专业财务能力单元。

## 2. 每个Skill必须包含

1. skill_id
2. 中文名称
3. 所属专业域
4. 输入对象
5. 数据来源
6. 前置完整性检查
7. 规则ID与规则版本
8. 确定性计算方法
9. 输出Result
10. Evidence
11. 风险等级
12. 允许自治等级
13. Guard
14. Verify规则
15. 测试样例
16. 失败处理
17. 生效/失效时间

## 3. 数值红线

关键财务数值必须来自：
- Python/SQL确定性计算
- 已批准规则引擎
- 正式数据对象

LLM仅允许：
- 解释
- 归纳
- 异常说明
- 建议方向
- 流程编排
- 报告草稿

LLM不得直接作为正式成本、毛利、现金、ROI、DSO等数值的计算来源。

## 4. 首批Skill

P0：
- quote_cost_calc 询价报价成本测算
- quote_price_band 报价价格区间测算
- order_economic_assessment 订单经济性评估
- order_margin_calc 订单毛利计算
- order_fac_forecast 订单完工成本预测
- quote_actual_variance 报价与实际差异分析
- ar_aging 应收账龄
- dso_calc DSO计算
- cash_7_30_90 7/30/90现金预测

P1：
- project_roi 项目ROI
- finance_opportunity 财务机会发现
- finance_review_pack 财经复盘生成

## 5. 开源能力采用策略

- OpenFPA：预测、企业记忆、模型迭代、预测回测
- OpenVariance：差异分析、驱动桥、周期复盘
- AR Skills：应收账龄、DSO、催收优先级
- FlowGuard-Sentinel：Guard、HITL、Verify、审计
- FinRobot：多智能体编排、确定性计算与LLM叙述分离

原则：不整套替代FAC，只提炼专业能力并适配AEOS Object/API/Event/Result/Evidence契约。

## 6. 质量门禁

Skill上线前必须：
- 有固定测试样例
- 数学结果可重复
- 规则版本明确
- Evidence可追溯
- 缺失数据不允许静默填0
- 缺失FX不允许默认1
- 历史结果不可覆盖
- 人工修正必须留痕
