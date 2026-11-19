# FAC 完整联调工作台实施计划

## 目标

在现有 FAC OFA Demo 的基础上，按已确认方案实现中文“完整联调工作台”：用真实本地 OFA 计算驱动 M02 EDP、M09 FAC、M13 Agent、M01 Guard、M10 POMS、FAC Verify、EBMS 的统一状态投影，并保留沙箱边界，不伪装成生产服务接入。

## 任务拆分

1. **统一联调契约与状态投影**
   - 增加阶段、智能体、DecisionCase、POMS Action、Verify 的 Pydantic 契约。
   - 从现有 `CalculationRun` / OFA 结果推导 V1、V2 和高风险付款阻断状态。
   - 用测试覆盖初始化、V1、V2 三个状态。

2. **扩展 Demo API**
   - 保持现有 `/api/v1/demo/state` 兼容。
   - 增加 `/api/v1/demo/integration`，返回完整联调投影。
   - 未初始化时返回 404，避免页面显示虚假完成状态。

3. **完成中文联调工作台**
   - 保留 AEOS 深色控制台和七个工作区。
   - 控制台展示完整主链、事件台账、阶段状态和对象投影。
   - 由同一 API 动态刷新事件、Agent Registry、DecisionCase、POMS Action、FAC Verify、EBMS 状态。
   - 明确“本地真实”和“沙箱投影”，突出 HMAC / 最小注册投影的正式边界。

4. **回归验证与交付**
   - 用 Playwright CLI 完成页面快照、运行链路、关键状态断言和截图。
   - 执行 API、模块、全量 pytest、ruff、compileall、diff 检查。
   - 补充 Demo 运行说明和最终交付记录。

## 验收标准

- 页面全中文，能看到原方案的七段闭环。
- 点击“运行联调演示”后，主链完成，OFA V1/V2 仍为 `46.00 / 52.00 CNY`。
- 付款智能体不可调度，高风险付款 DecisionCase 为“已阻断”。
- POMS 普通动作显示执行反馈已回流 FAC。
- Verify 显示 100% 证据覆盖率、Value Ledger 和 EBMS 已消费。
- 事件回放保持幂等，不重复生成财经事实。
