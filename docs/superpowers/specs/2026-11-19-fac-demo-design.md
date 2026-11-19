# FAC 财经自治 Demo 设计

状态：已确认

日期：2026-11-19

## 1. 意图

在现有 FAC FastAPI、EDP fixture、OFA 计算引擎和 Calculation 版本化实现之上，提供一个可浏览器操作的真实 Demo，展示订单进入 FAC 后的计划成本计算、报价重算、历史结果保留和事件幂等重放。

## 2. 目标

- 使用真实 `OFAEngine` 计算，不使用固定金额冒充结果。
- 展示 `CalculationSnapshot`、`CalculationRun`、`CalculationResult` 及输入引用。
- 用价格版本变化演示 V1 → V2 重算，旧结果保持不变。
- 用 `QuoteRecalculationRequired` 演示事件验证重放幂等。
- 提供简单、可响应式的浏览器工作台和 Demo API。

## 3. 非目标

- 不接入真实 M02、M04、M13 或外部 EDP。
- 不实现生产鉴权、Outbox 异步投递、自动重试和数据清理。
- 不扩展实际成本、毛利、AR、回款等后续模块。
- 不修改或覆盖现有用户未提交改动。

## 4. 方案

Demo 使用固定的 `demo-tenant` 和 `demo-edp` 数据。`DemoService` 负责初始化演示对象、记录演示事件、组装冻结输入引用，并调用已有 `CalculationService` 和 `OFAEngine`。演示 API 使用 `/api/v1/demo` 前缀，页面使用 `/demo/fac`，默认受 `FAC_DEMO_ENABLED` 控制。

初始数据为订单 `ORD-1001`：数量 2、BOM 每件 3kg 钢材、V1 材料价格 4 CNY/kg、人工 20 CNY、费用 2 CNY，计划总成本为 46.00 CNY。V2 材料价格为 5 CNY/kg，重算总成本为 52.00 CNY。

## 5. 交互流程

1. 初始化 Demo 数据。
2. 运行初次报价计算并显示 V1。
3. 模拟材料价格修正并显示 V2，同时保留 V1。
4. 重放相同事件，显示已复用既有结果且没有重复记录。
5. 在页面时间线查看事件、CalculationRun、Snapshot、Result、版本和 checksum。

## 6. 安全边界

- reset 只清理 `demo-tenant` 范围内的数据。
- Demo 只使用本地 SQLite 和内置样例，不携带真实密钥。
- 生产环境默认关闭 Demo 路由。
- 页面和 API 明确标识 Demo，不作为生产财经接口。

