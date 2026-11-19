# AEOS M09 FAC 财经自治中心

本仓库是 FAC 正式产品化服务，当前阶段聚焦订单财经分析：从 M02 EDP 接入订单、BOM、物料价格、人工、费用和汇率事实，经过 OFA 计算生成版本化财经结果，并提供规则、期间、事件、证据和外部处理状态查询。

## 本地安装

要求 Python 3.11。在仓库根目录执行：

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
Copy-Item .env.example .env
```

正式运行配置使用以下环境变量：

- `FAC_DATABASE_URL`：数据库连接，默认建议使用 `sqlite:///./data/fac.db`。
- `FAC_FUNCTIONAL_CURRENCY`：本位币，默认 `CNY`。
- `FAC_ENVIRONMENT`：运行环境标识，默认 `development`。
- `FAC_TENANT_ID`：正式工作台默认租户，默认 `default-tenant`。
- `FAC_DEMO_ENABLED`：是否启用测试 Demo，正式环境必须为 `false`。

## 正式本地运行

使用正式脚本会先执行迁移，再显式导入 Phase 1 EDP 夹具，最后启动服务：

```powershell
.\scripts\run_fac.ps1
```

正式入口：

- 工作台：`http://127.0.0.1:8000/fac`
- 健康检查：`http://127.0.0.1:8000/health`
- 正式概览：`GET /api/v1/fac/overview`
- 订单：`GET /api/v1/fac/orders`
- 订单计算：`POST /api/v1/fac/orders/{order_id}/calculations`
- 结果证据：`GET /api/v1/fac/results/{result_id}/evidence`
- 待外部处理：`GET /api/v1/fac/external-requests`

正式服务不会在启动时自动插入固定订单、规则或 Demo 数据；数据必须通过 EDP 接口、夹具导入或后续外部系统接口进入。

## 数据生命周期

执行迁移：

```powershell
$env:FAC_DATABASE_URL = "sqlite:///./data/fac.db"
python -m alembic upgrade head
```

重复执行 `upgrade head` 是安全的。升级前建议备份 SQLite 文件：

```powershell
Copy-Item .\data\fac.db .\data\backup\fac-$(Get-Date -Format yyyyMMdd-HHmmss).db
```

恢复时先停止服务，再替换数据库文件并重新执行健康检查：

```powershell
Copy-Item .\data\backup\fac-YYYYMMDD-HHmmss.db .\data\fac.db -Force
python -m alembic upgrade head
```

如需回滚迁移，只允许在备份确认后执行：

```powershell
python -m alembic downgrade -1
```

生产环境建议将 `/app/data` 挂载为持久化卷，并在发布前完成数据库备份和迁移演练。

## 测试 Demo（仅测试用途）

Demo 与正式系统隔离，使用独立的 `fac_demo.db` 和 `demo-tenant`，不会代表正式工作台数据。运行：

```powershell
.\scripts\run_fac_demo.ps1
```

打开 `http://127.0.0.1:8000/demo/fac`。Demo 路由由 `FAC_DEMO_ENABLED=true` 显式开启，正式环境不得开启。

## 验证

```powershell
ruff check src tests
python -m pytest -q
python -m alembic check
```

当前已经具备本系统内的订单财经计算、版本化结果、事件幂等、规则/期间模型、证据查询和外部请求状态；M13 智能体、M01 防护、M10 POMS、EBMS 等外部系统保留正式接口和 `待接入/待外部处理` 状态，待接口资料确认后接入。
