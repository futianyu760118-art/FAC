# FAC 正式产品化发布记录

## 发布信息

- 发布日期：2026-11-19
- 发布目标：腾讯云同一公网入口 `http://150.158.13.110:18000/fac`
- 运行容器：`fac-fac-1`
- 镜像：`fac-formal:20261119-r6`
- 镜像摘要：`sha256:d9df587235b9c1676af497d8a2b03d4d1b6cdf79fc78aeb6082dada226ec309f`
- 正式数据目录：`/home/ubuntu/fac-formal-data-20261119-prod`
- 数据库：`/app/data/fac.db`，由宿主机目录持久化
- 正式配置：`FAC_DEMO_ENABLED=false`、`FAC_ENVIRONMENT=production`、`FAC_TENANT_ID=tenant-a`

## 发布前验证

- `ruff check src tests`：通过。
- `python -m pytest -q`：94 passed，1 warning。
- `python -m pytest tests/regression/test_formal_product_boundary.py -q`：4 passed。
- `python -m alembic check`：通过。
- Docker 隔离容器：迁移、`/health`、正式概览、空正式订单和重启后持久化均通过。
- 腾讯云 canary：临时端口 `18001` 通过页面、OpenAPI、EDP 夹具导入、订单计算、证据查询和重启验证。

## 正式验收

- `GET /health`：200，`service=fac`。
- `GET /api/v1/fac/overview`：200，`status=ready`，`environment=production`，`demo_enabled=false`。
- `GET /api/v1/fac/orders`：正式发布后通过显式 EDP 夹具导入得到 `ORD-001`。
- 订单财经计算：`Order:ORD-001:plan:v1`，总成本 `834.00 CNY`。
- 证据查询：`WAITING_EVIDENCE`，覆盖率 `0%`。外部证据未接入时没有伪造“已验证”。
- 公网页面：`/fac` 正式文案、正式 API hooks、`计算订单` 和 `待外部处理` 可见；旧 Demo 文案不可见。
- 前台工作台：首屏以订单财经分析为主，支持选择订单、查看销售金额/计划成本/预计毛利、计算订单、提交复核、查看证据覆盖率和待外部处理；系统事件、智能体协同、财经标准、运行设置和外部接口等后台模块默认收纳到“更多模块”。
- 订单核算：保留原 OFA 订单核算模块为一级导航，独立展示核算版本、核算规则、财经期间、销售/成本/毛利和冻结输入引用，并保留“重新核算订单”入口。
- 浏览器验收：公网首屏显示 `订单财经分析`、`ORD-001`、`834.00 CNY`、`0%` 证据覆盖率；点击“系统详情”可进入后台台账；点击“计算订单”无 console error。
- 配置导航验收：展开“更多模块”后可进入“标准 / 设置 / 接口”，集中查看财经规则、期间、运行配置和 M02/M13/M01/M10/EBMS 接入状态。
- 重启验收：重启 `fac-fac-1` 后 `ORD-001` 和 `Order:ORD-001:plan:v1` 仍可查询。

## 旧版本保留与回滚

旧公网容器和上一版正式容器均已停止并保留：

- 容器：`fac-fac-demo-rollback-20261119`
- 镜像：`fac-demo:20261119-fast2`
- 上一版正式回滚容器：`fac-fac-formal-r1-rollback-20261119`
- 上一版正式镜像：`fac-formal:20261119`
- 本次发布前正式回滚容器：`fac-fac-formal-r5-rollback-20261119`
- 本次发布前正式镜像：`fac-formal:20261119-r5`
- 旧 Demo 数据备份：`/home/ubuntu/fac-rollback-20261119/fac_demo.db`
- 旧容器与镜像 inspect：同目录下的 `old-container-inspect.json`、`old-image-inspect.json`

如需回滚到上一版正式容器，先在腾讯云主机执行：

```bash
docker stop fac-fac-1
docker rename fac-fac-1 fac-fac-formal-r6-failed-20261119
docker rename fac-fac-formal-r5-rollback-20261119 fac-fac-1
docker start fac-fac-1
curl -fsS http://127.0.0.1:18000/health
```

如需回滚到发布前的临时 Demo，则停止正式容器后，将 `fac-fac-demo-rollback-20261119` 改名为 `fac-fac-demo-1` 并启动；其独立数据库备份位于 `/home/ubuntu/fac-rollback-20261119/fac_demo.db`。恢复正式版本时，停止旧容器后重新将正式容器以 `fac-fac-1`、`18000:8000` 和 `/home/ubuntu/fac-formal-data-20261119-prod:/app/data` 启动，并执行 `python -m alembic upgrade head`。

## 当前边界

本次发布包含 FAC 本地可完成的 EDP-first 订单财经计算、规则/期间查询、版本化结果、事件幂等、证据查询和外部请求状态。M13 Agent、M01 Guard、M10 POMS、EBMS 的生产接口保留正式边界，当前显示 `待接入` 或 `待外部处理`，后续按接口资料接入。
