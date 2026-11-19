"""AEOS-style integrated FAC workbench for the formal product entry point."""


def render_fac_page() -> str:
    """Return the formal M09 FAC workbench while preserving the original layout."""
    html = r'''<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <link rel="icon" href="data:,">
  <title>AEOS V7.2.2 · M09 FAC</title>
  <style>
    :root { --bg:#090f18; --panel:#101b29; --line:#24364a; --ink:#e8f0f7; --muted:#7890a5;
      --green:#74e2ae; --green-bg:rgba(116,226,174,.12); --blue:#70b8ff; --amber:#f0bd69;
      --red:#ff817d; --purple:#b895ff; --shadow:0 18px 60px rgba(0,0,0,.26); }
    * { box-sizing:border-box; }
    body { margin:0; min-width:320px; color:var(--ink); background:radial-gradient(circle at 78% -10%, #1c3550 0, transparent 34%), var(--bg); font:13px/1.5 Inter, ui-sans-serif, system-ui, -apple-system, "Segoe UI", sans-serif; }
    button, select { font:inherit; } button { border:0; cursor:pointer; }
    .app { min-height:100vh; display:grid; grid-template-columns:238px minmax(0,1fr); }
    .rail { display:flex; flex-direction:column; padding:22px 14px; background:rgba(7,14,23,.92); border-right:1px solid var(--line); }
    .brand { display:flex; align-items:center; gap:11px; padding:4px 10px 23px; border-bottom:1px solid var(--line); }
    .brand-mark { width:38px; height:38px; display:grid; place-items:center; color:#07131b; background:var(--green); border-radius:10px; font-size:19px; font-weight:900; }
    .brand strong { display:block; font-size:17px; letter-spacing:.08em; } .brand small { display:block; margin-top:3px; color:var(--muted); font-size:10px; letter-spacing:.12em; }
    .module { padding:22px 10px 8px; color:#4e6880; font-size:10px; letter-spacing:.16em; text-transform:uppercase; }
    .nav { display:grid; gap:4px; } .nav button { display:flex; align-items:center; gap:11px; width:100%; padding:11px 12px; color:#9ab0c1; background:transparent; border-radius:8px; text-align:left; transition:color .16s ease, background .16s ease, transform .16s ease; }
    .nav button:hover { color:#fff; background:#17283a; transform:translateX(2px); } .nav button.active { color:var(--green); background:var(--green-bg); box-shadow:inset 2px 0 var(--green); }
    .nav-icon { width:17px; color:inherit; text-align:center; font-size:15px; } .rail-bottom { margin-top:auto; padding:16px 10px 0; color:var(--muted); border-top:1px solid var(--line); font-size:11px; }
    .rail-bottom strong { display:block; margin-bottom:3px; color:var(--ink); font-size:12px; }
    .main { min-width:0; } .topbar { height:68px; display:flex; align-items:center; justify-content:space-between; padding:0 30px; background:rgba(10,18,29,.84); border-bottom:1px solid var(--line); backdrop-filter:blur(16px); position:sticky; top:0; z-index:5; }
    .crumb { display:flex; align-items:center; gap:9px; color:#d9e6ef; font-weight:720; } .crumb span { color:var(--muted); font-weight:500; }
    .top-actions { display:flex; align-items:center; gap:18px; color:var(--muted); font-size:12px; } .environment { display:flex; align-items:center; gap:7px; color:var(--green); }
    .pulse { width:7px; height:7px; background:var(--green); border-radius:50%; box-shadow:0 0 0 4px rgba(116,226,174,.12); } .tenant { padding:7px 10px; color:#b6c9d6; border:1px solid var(--line); border-radius:6px; }
    .page { width:min(1500px, calc(100% - 60px)); margin:0 auto; padding:28px 0 55px; } .page-head { display:flex; align-items:end; justify-content:space-between; gap:18px; margin-bottom:25px; }
    h1,h2,h3,p { margin:0; } h1 { font-size:30px; letter-spacing:-.04em; } h2 { font-size:17px; letter-spacing:-.02em; } h3 { font-size:13px; }
    .eyebrow { color:var(--green); font-size:10px; font-weight:800; letter-spacing:.18em; text-transform:uppercase; } .subtitle { margin-top:7px; color:var(--muted); }
    .head-right { display:flex; align-items:center; gap:9px; } .button { padding:9px 13px; color:#a9bfd0; background:#162639; border:1px solid #2d4258; border-radius:7px; font-weight:720; transition:transform .16s ease, background .16s ease, border-color .16s ease; }
    .button:hover { color:#fff; background:#1c3248; border-color:#44627e; transform:translateY(-1px); } .button.primary { color:#08131a; background:var(--green); border-color:var(--green); } .button:disabled { cursor:wait; opacity:.6; }
    .state { display:flex; align-items:center; gap:7px; color:var(--green); font-size:12px; } .state .pulse { width:6px; height:6px; }
    .pane { display:none; animation:appear .18s ease both; } .pane.active { display:block; } @keyframes appear { from { opacity:0; transform:translateY(5px); } to { opacity:1; transform:none; } }
    .panel { background:linear-gradient(135deg, rgba(19,35,52,.96), rgba(13,25,39,.96)); border:1px solid var(--line); border-radius:10px; box-shadow:var(--shadow); }
    .panel-head { display:flex; align-items:start; justify-content:space-between; gap:14px; padding:18px 19px; border-bottom:1px solid var(--line); } .panel-head p { margin-top:4px; color:var(--muted); font-size:11px; } .panel-body { padding:19px; }
    .flow-panel { padding:20px; overflow:hidden; } .flow-header { display:flex; align-items:start; justify-content:space-between; gap:16px; margin-bottom:22px; } .flow-header p { margin-top:5px; color:var(--muted); font-size:12px; }
    .flow-meta { color:#7c93a5; font:11px ui-monospace, SFMono-Regular, Consolas, monospace; text-align:right; }
    .flow { display:grid; grid-template-columns:1fr 24px 1fr 24px 1.05fr 24px 1fr 24px 1fr 24px 1fr 24px 1fr; gap:7px; align-items:center; min-width:1080px; }
    .flow-node { min-height:126px; padding:15px 13px; background:#122337; border:1px solid #2a4057; border-radius:8px; position:relative; transition:border-color .2s ease, background .2s ease, box-shadow .2s ease; }
    .flow-node.done { background:rgba(67,163,120,.13); border-color:#397d63; box-shadow:0 0 0 1px rgba(116,226,174,.1), 0 0 24px rgba(116,226,174,.08); } .flow-node.running { border-color:var(--amber); box-shadow:0 0 0 1px rgba(240,189,105,.12); }
    .node-kicker { color:#607b91; font:10px ui-monospace, SFMono-Regular, Consolas, monospace; letter-spacing:.08em; } .node-name { margin-top:9px; font-size:16px; font-weight:780; } .node-desc { min-height:35px; margin-top:7px; color:var(--muted); font-size:11px; }
    .node-status { display:flex; align-items:center; gap:6px; margin-top:12px; color:#647f94; font-size:10px; } .node-status i { width:6px; height:6px; background:#50667a; border-radius:50%; } .flow-node.done .node-status { color:var(--green); } .flow-node.done .node-status i { background:var(--green); box-shadow:0 0 0 3px rgba(116,226,174,.1); }
    .arrow { color:#4c6a84; font-size:20px; text-align:center; } .arrow.done { color:var(--green); }
    .runbook { display:grid; grid-template-columns:repeat(4,1fr); gap:10px; margin-top:16px; } .run-step { display:flex; gap:10px; padding:12px; background:#0f1c2b; border:1px solid var(--line); border-radius:7px; }
    .run-no { width:23px; height:23px; display:grid; place-items:center; flex:0 0 auto; color:#09131b; background:#456078; border-radius:50%; font-size:10px; font-weight:850; } .run-step.done .run-no { background:var(--green); }
    .run-step strong { display:block; color:#cce0ec; font-size:12px; } .run-step small { display:block; margin-top:2px; color:var(--muted); font-size:10px; }
    .dashboard-grid { display:grid; grid-template-columns:1.25fr .75fr; gap:17px; margin-top:17px; } .signal-grid { display:grid; grid-template-columns:repeat(4,1fr); gap:10px; margin-top:17px; }
    .signal { padding:15px; background:#0f1c2b; border:1px solid var(--line); border-radius:8px; } .signal-top { display:flex; align-items:center; justify-content:space-between; color:var(--muted); font-size:11px; } .signal strong { display:block; margin-top:10px; font-size:20px; letter-spacing:-.04em; } .signal small { display:block; margin-top:4px; color:var(--muted); font-size:10px; }
    .good { color:var(--green); } .warn { color:var(--amber); } .bad { color:var(--red); } .blue { color:var(--blue); } .purple { color:var(--purple); }
    .ledger { overflow:auto; } table { width:100%; border-collapse:collapse; } th, td { padding:11px 18px; border-bottom:1px solid var(--line); text-align:left; white-space:nowrap; } th { color:#6f899d; font-size:10px; font-weight:650; letter-spacing:.08em; text-transform:uppercase; } td { color:#bed0dc; font-size:12px; } tr:last-child td { border-bottom:0; }
    code { color:#9cc2df; font:11px ui-monospace, SFMono-Regular, Consolas, monospace; } .badge { display:inline-block; padding:3px 7px; border-radius:5px; font-size:10px; font-weight:780; } .badge.good { background:rgba(116,226,174,.13); } .badge.warn { background:rgba(240,189,105,.14); } .badge.bad { background:rgba(255,129,125,.13); } .badge.blue { background:rgba(112,184,255,.13); }
    .stat-cards { display:grid; grid-template-columns:repeat(3,1fr); gap:12px; } .stat-card { padding:18px; background:#101f30; border:1px solid var(--line); border-radius:8px; } .stat-card label { color:var(--muted); font-size:11px; } .stat-card strong { display:block; margin-top:8px; font-size:25px; } .list { display:grid; gap:9px; }
    .list-row { display:flex; align-items:center; justify-content:space-between; gap:12px; padding:13px 14px; background:#0f1c2b; border:1px solid var(--line); border-radius:7px; } .list-row strong { display:block; font-size:12px; } .list-row small { display:block; margin-top:3px; color:var(--muted); font-size:10px; }
    .projection-grid { display:grid; grid-template-columns:repeat(3,1fr); gap:10px; }
    .projection-card { padding:13px 14px; background:#0f1c2b; border:1px solid var(--line); border-radius:7px; }
    .projection-card strong { display:block; margin-top:6px; font-size:14px; }
    .projection-card small { display:block; margin-top:4px; color:var(--muted); font-size:10px; }
    .projection-card code { display:block; margin-top:8px; color:#7fa4bf; }
    .projection-list { display:grid; gap:8px; }
    .projection-row { display:flex; align-items:flex-start; justify-content:space-between; gap:16px; padding:11px 12px; background:#0f1c2b; border:1px solid var(--line); border-radius:7px; }
    .projection-row strong { display:block; font-size:12px; }
    .projection-row small { display:block; margin-top:4px; color:var(--muted); font-size:10px; }
    .projection-row .right { flex:0 0 auto; text-align:right; }
    .subtle-label { color:#6f899d; font-size:10px; letter-spacing:.08em; text-transform:uppercase; }
    @media (max-width:760px) { .projection-grid { grid-template-columns:1fr; } }
    .activity { display:grid; gap:0; } .activity-row { display:grid; grid-template-columns:115px 150px 1fr; gap:14px; padding:13px 0; border-bottom:1px solid var(--line); } .activity-row:last-child { border-bottom:0; } .activity-time { color:#637d91; font:10px ui-monospace, SFMono-Regular, Consolas, monospace; } .activity-row p { color:#b4c7d4; font-size:12px; }
    .toast { position:fixed; right:24px; bottom:24px; z-index:20; padding:12px 15px; color:#08131a; background:var(--green); border-radius:7px; box-shadow:var(--shadow); transform:translateY(15px); opacity:0; pointer-events:none; transition:opacity .18s ease, transform .18s ease; } .toast.show { opacity:1; transform:none; }
    @media (max-width:1100px) { .app { grid-template-columns:82px minmax(0,1fr); } .rail { padding:18px 10px; } .brand { justify-content:center; padding-left:0; padding-right:0; } .brand > div:not(.brand-mark), .module, .nav button span:not(.nav-icon), .rail-bottom { display:none; } .nav button { justify-content:center; } .page { width:calc(100% - 36px); } }
    @media (max-width:760px) { .topbar { padding:0 16px; } .top-actions { gap:8px; } .tenant { display:none; } .page { width:calc(100% - 24px); padding-top:22px; } .page-head { display:block; } .head-right { margin-top:15px; justify-content:flex-start; } .dashboard-grid { grid-template-columns:1fr; } .signal-grid, .stat-cards { grid-template-columns:repeat(2,1fr); } .runbook { grid-template-columns:1fr 1fr; } .flow-panel { overflow:auto; } .activity-row { grid-template-columns:1fr; gap:4px; } }
    @media (max-width:480px) { .app { grid-template-columns:1fr; } .rail { position:sticky; top:0; z-index:8; height:61px; flex-direction:row; align-items:center; overflow:auto; padding:9px 11px; } .brand { flex:0 0 auto; border:0; padding:0; } .brand-mark { width:34px; height:34px; } .nav { display:flex; } .nav button { width:40px; height:38px; flex:0 0 auto; padding:0; } .topbar { height:61px; } .crumb { font-size:12px; } .signal-grid, .stat-cards { grid-template-columns:1fr 1fr; gap:8px; } .signal { padding:12px; } .signal strong { font-size:17px; } .runbook { grid-template-columns:1fr; } }
    @media (prefers-reduced-motion:reduce) { *, *::before, *::after { animation-duration:.01ms !important; transition-duration:.01ms !important; } }
  </style>
</head>
<body>
  <div class="app">
    <aside class="rail" aria-label="AEOS FAC 导航"><div class="brand"><div class="brand-mark">F</div><div><strong>FAC</strong><small>AEOS M09 · 财经自治中心</small></div></div><div class="module">M09 工作台</div><nav class="nav"><button class="active" data-pane="control" aria-current="page"><span class="nav-icon">⌘</span><span>控制台</span></button><button data-pane="results"><span class="nav-icon">▣</span><span>财经结果</span></button><button data-pane="guards"><span class="nav-icon">◇</span><span>防护 / 决策</span></button><button data-pane="actions"><span class="nav-icon">→</span><span>POMS 动作</span></button><button data-pane="evidence"><span class="nav-icon">▤</span><span>证据</span></button><div class="nav-more" data-nav-more><button class="nav-more-toggle" type="button" data-nav-more-toggle aria-expanded="false"><span class="nav-icon">＋</span><span>更多模块</span></button><div class="nav-secondary" data-nav-secondary><button data-pane="events"><span class="nav-icon">↯</span><span>系统详情</span></button><button data-pane="agents"><span class="nav-icon">◌</span><span>智能体协同</span></button><button data-pane="settings"><span class="nav-icon">⚙</span><span>标准 / 设置 / 接口</span></button></div></div></nav><div class="rail-bottom"><strong>AEOS V7.2.2</strong><span>本地联调沙箱</span></div></aside>
    <section class="main"><header class="topbar"><div class="crumb"><span>AEOS</span><b>/</b><span>M09</span><b>/</b> FAC 财经自治中心</div><div class="top-actions"><span class="environment"><i class="pulse"></i><span id="system-status">系统在线</span></span><span class="tenant">租户：demo-tenant</span><span>本地</span></div></header>
      <main class="page"><div class="toast" id="toast" role="status"></div>
        <section class="pane active" data-pane-panel="control"><div class="page-head"><div><div class="eyebrow">M09 · 联调控制台</div><h1>FAC 财经自治中心</h1><p class="subtitle">业务事实进入 EDP，FAC 负责财经判断，智能体、防护与动作形成可验证闭环。</p></div><div class="head-right"><span class="state"><i class="pulse"></i><span id="run-state">A0 · 观察</span></span><button class="button" id="replay">重放最近事件</button><button class="button primary" id="run">运行联调演示</button></div></div>
          <article class="panel flow-panel"><div class="flow-header"><div><h2>真实系统联调主干</h2><p>CRM / PLM → M02 EDP → FAC → M13 Agent → M01 Guard → M10 POMS → Verify → EBMS</p></div><div class="flow-meta">关联编号：FAC-DEMO-2025-01<br>幂等：已启用</div></div><div class="flow" id="flow"><div class="flow-node" data-node="source"><div class="node-kicker">来源系统</div><div class="node-name">CRM / PLM</div><div class="node-desc">订单 · 报价 · 物料清单<br>业务事实产生</div><div class="node-status"><i></i><span>待触发</span></div></div><div class="arrow">›</div><div class="flow-node" data-node="edp"><div class="node-kicker">M02</div><div class="node-name">EDP</div><div class="node-desc">对象 · 事件<br>证据 · 审计</div><div class="node-status"><i></i><span>待标准化</span></div></div><div class="arrow">›</div><div class="flow-node" data-node="fac"><div class="node-kicker">M09</div><div class="node-name">FAC</div><div class="node-desc">OFA · 毛利<br>财经结果</div><div class="node-status"><i></i><span>待计算</span></div></div><div class="arrow">›</div><div class="flow-node" data-node="agent"><div class="node-kicker">M13</div><div class="node-name">智能体</div><div class="node-desc">CFO / 成本智能体<br>技能注册</div><div class="node-status"><i></i><span>待建议</span></div></div><div class="arrow">›</div><div class="flow-node" data-node="guard"><div class="node-kicker">M01</div><div class="node-name">防护</div><div class="node-desc">权限控制<br>决策案例</div><div class="node-status"><i></i><span>待判定</span></div></div><div class="arrow">›</div><div class="flow-node" data-node="poms"><div class="node-kicker">M10</div><div class="node-name">POMS</div><div class="node-desc">动作 · 待办<br>执行反馈</div><div class="node-status"><i></i><span>待下发</span></div></div><div class="arrow">›</div><div class="flow-node" data-node="verify"><div class="node-kicker">验证</div><div class="node-name">验证</div><div class="node-desc">结果 · 投入产出<br>价值台账</div><div class="node-status"><i></i><span>待验证</span></div></div></div><div class="runbook"><div class="run-step" data-step="1"><div class="run-no">01</div><div><strong>事实进入 EDP</strong><small>对象 / 事件 / 证据</small></div></div><div class="run-step" data-step="2"><div class="run-no">02</div><div><strong>FAC 计算判断</strong><small>OFA 结果 V1 / V2</small></div></div><div class="run-step" data-step="3"><div class="run-no">03</div><div><strong>智能体 + 防护</strong><small>建议与权限分离</small></div></div><div class="run-step" data-step="4"><div class="run-no">04</div><div><strong>动作 + 验证</strong><small>POMS 执行与回证</small></div></div></div></article>
          <article class="panel" style="margin-top:17px" id="integration-overview"><div class="panel-head"><div><h2>完整联调投影</h2><p>同一份状态投影串联 M02 EDP、M09 FAC、M13 Agent、M01 Guard、M10 POMS、FAC Verify 与 EBMS。</p></div><span class="badge blue" id="integration-mode">本地沙箱</span></div><div class="panel-body"><div class="projection-grid"><div class="projection-card"><span class="subtle-label">关联编号</span><strong id="integration-correlation">FAC-DEMO-2025-01</strong><small>跨系统追踪主键</small></div><div class="projection-card"><span class="subtle-label">幂等策略</span><strong id="integration-idempotency">已启用</strong><small>事件可安全回放</small></div><div class="projection-card"><span class="subtle-label">验证结果</span><strong id="integration-verify">待验证</strong><small id="integration-evidence">证据覆盖率 0%</small></div></div><div class="projection-list" id="integration-stage-list" style="margin-top:10px"></div></div></article>
          <div class="signal-grid"><div class="signal"><div class="signal-top"><span>M02 EDP</span><b class="good">就绪</b></div><strong>2,418</strong><small>对象 · 36 个事件 · 发件箱已同步</small></div><div class="signal"><div class="signal-top"><span>M13 智能体</span><b class="blue">注册</b></div><strong>4 / 5</strong><small>可调度智能体 · 服务签名已启用</small></div><div class="signal"><div class="signal-top"><span>M01 防护</span><b class="purple">策略</b></div><strong>100%</strong><small>高风险动作必须审批</small></div><div class="signal"><div class="signal-top"><span>M10 POMS</span><b class="good">在线</b></div><strong>12</strong><small>进行中动作 · 0 次下发失败</small></div></div>
          <div class="dashboard-grid"><article class="panel"><div class="panel-head"><div><h2>事件台账</h2><p>可重放、可追踪、幂等的跨系统事件记录</p></div><button class="button" data-pane-link="events">查看全部</button></div><div class="ledger"><table><thead><tr><th>事件</th><th>来源</th><th>目标</th><th>关联编号</th><th>状态</th></tr></thead><tbody><tr><td><code>QuoteRecalculationRequired</code></td><td>CRM</td><td>FAC-OFA</td><td><code>FAC-DEMO-2025-01</code></td><td><span class="badge good" id="ledger-status">待处理</span></td></tr><tr><td><code>BOMReleased</code></td><td>PLM</td><td>EDP</td><td><code>PLM-2025-0118</code></td><td><span class="badge good">已接收</span></td></tr><tr><td><code>MarginRiskDetected</code></td><td>FAC</td><td>M01 Guard</td><td><code>RISK-250124-02</code></td><td><span class="badge warn">待复核</span></td></tr></tbody></table></div></article><article class="panel"><div class="panel-head"><div><h2>运行轨迹</h2><p>最近一次链路执行状态</p></div><span class="badge blue" id="trace-badge">空闲</span></div><div class="panel-body"><div class="activity"><div class="activity-row"><span class="activity-time">10:05:12.402</span><code>edp.object.project</code><p id="trace-1">等待订单 / 物料清单投影</p></div><div class="activity-row"><span class="activity-time">10:05:12.671</span><code>fac.ofa.calculate</code><p id="trace-2">等待计算运行</p></div><div class="activity-row"><span class="activity-time">10:05:13.018</span><code>m01.guard.check</code><p id="trace-3">等待决策案例</p></div><div class="activity-row"><span class="activity-time">10:05:13.284</span><code>verify.evidence</code><p id="trace-4">等待财经结果验证</p></div></div></div></article></div>
        </section>
        <section class="pane" data-pane-panel="events"><div class="page-head"><div><div class="eyebrow">M02 · 事件与回放</div><h1>事件总线</h1><p class="subtitle">所有事件都有：关联编号、幂等键、来源与证据引用。</p></div><div class="head-right"><button class="button" data-action="refresh">刷新事件</button><button class="button primary" id="run-events">运行示例链路</button></div></div><article class="panel" id="integration-events"><div class="panel-head"><div><h2>事件台账</h2><p>回放不会产生重复财经事实</p></div><span class="badge good">幂等</span></div><div class="ledger"><table><thead><tr><th>事件编号</th><th>类型</th><th>来源</th><th>目标</th><th>关联编号</th><th>幂等键</th><th>状态</th></tr></thead><tbody id="integration-event-list"><tr><td><code>demo-event-v1</code></td><td>QuoteRecalculationRequired</td><td>CRM</td><td>M09 FAC</td><td><code>FAC-DEMO-2025-01</code></td><td><code>demo-key-v1</code></td><td><span class="badge good">待处理</span></td></tr><tr><td><code>plm-bom-0118</code></td><td>BOMReleased</td><td>PLM</td><td>M02 EDP</td><td><code>PLM-2025-0118</code></td><td><code>plm-key-0118</code></td><td><span class="badge good">待确认</span></td></tr><tr><td><code>demo-margin-risk-v2</code></td><td>MarginRiskDetected</td><td>M09 FAC</td><td>M01 Guard</td><td><code>RISK-250124-02</code></td><td><code>risk-key-250124-02</code></td><td><span class="badge warn">待复核</span></td></tr></tbody></table></div></article></section>
        <section class="pane" data-pane-panel="results"><div class="page-head"><div><div class="eyebrow">M09 · 财经结果</div><h1>财经结果</h1><p class="subtitle">FAC 负责财经专业结果，EBMS 只消费结果与证据。</p></div><div class="head-right"><a class="button" href="/demo/fac">打开 OFA 明细</a><button class="button primary" id="run-results">运行 OFA 计算</button></div></div><div class="stat-cards"><div class="stat-card"><label>计划成本 V1</label><strong id="result-v1">46.00 CNY</strong><span class="good">计算快照已冻结</span></div><div class="stat-card"><label>计划成本 V2</label><strong id="result-v2">52.00 CNY</strong><span class="good">物料价格修订版 2</span></div><div class="stat-card"><label>证据覆盖率</label><strong>100%</strong><span class="good">订单 / 物料清单 / 规则 / 价格</span></div></div><article class="panel" style="margin-top:17px"><div class="panel-head"><div><h2>财经结果契约</h2><p>结果 → 快照 → 规则 → 来源对象 → 证据</p></div><span class="badge good">已验证链路</span></div><div class="panel-body"><div class="list"><div class="list-row"><div><strong>订单毛利结果 · ORD-1001</strong><small>管理财经 · 本位币 CNY</small></div><code>result:plan:v2</code></div><div class="list-row"><div><strong>规则注册表 · OFA_PLAN_COST</strong><small>规则版本：v1 · 生效日期：2025-01-01</small></div><code>rule:v1</code></div><div class="list-row"><div><strong>快照 · 物料价格</strong><small>PRICE-1001 · 修订版 2 · 已挂接证据</small></div><code>snap:price:v2</code></div></div></div></article></section>
        <section class="pane" data-pane-panel="agents"><div class="page-head"><div><div class="eyebrow">M13 · 智能体注册中心</div><h1>智能体注册中心</h1><p class="subtitle">FAC 只调用可调度智能体，不模拟网页登录，不绕过服务间认证。</p></div><div class="head-right"><span class="state"><i class="pulse"></i>服务间签名已连接</span></div></div><article class="panel"><div class="panel-head"><div><h2>可调度智能体</h2><p>最小注册投影 · 能力 · 策略</p></div><span class="badge blue">4 / 5 就绪</span></div><div class="panel-body"><div class="list"><div class="list-row"><div><strong>CFO 智能体</strong><small>财经汇总 · 财经解释 · A0 观察</small></div><span class="badge good">就绪</span></div><div class="list-row"><div><strong>成本智能体</strong><small>计算计划成本 · 识别成本异常 · A1 建议</small></div><span class="badge good">就绪</span></div><div class="list-row"><div><strong>毛利智能体</strong><small>计算订单毛利 · 识别毛利风险 · A1 建议</small></div><span class="badge good">就绪</span></div><div class="list-row"><div><strong>应收智能体</strong><small>计算应收账龄 · 预测回款 · A1 建议</small></div><span class="badge good">就绪</span></div><div class="list-row"><div><strong>付款智能体</strong><small>付款执行 · 高风险动作</small></div><span class="badge warn">受保护</span></div></div></div></article></section>
        <section class="pane" data-pane-panel="guards"><div class="page-head"><div><div class="eyebrow">M01 · 策略与决策</div><h1>防护 / 决策</h1><p class="subtitle">智能体建议与高风险财经动作执行分离。</p></div><div class="head-right"><span class="badge good">策略引擎在线</span></div></div><div class="stat-cards"><div class="stat-card"><label>今日策略检查</label><strong>128</strong><span class="good">0 次绕过</span></div><div class="stat-card"><label>待审批</label><strong>7</strong><span class="warn">2 个高风险</span></div><div class="stat-card"><label>职责分离覆盖率</label><strong>100%</strong><span class="good">发起人 → 验证人</span></div></div><article class="panel" style="margin-top:17px"><div class="panel-head"><div><h2>决策案例队列</h2><p>风险结果进入防护层，不能由智能体自行验证。</p></div></div><div class="panel-body"><div class="list"><div class="list-row"><div><strong>订单 B 毛利率低于底线</strong><small>发起智能体：毛利智能体 · 责任人：订单财经组</small></div><span class="badge warn">复核人</span></div><div class="list-row"><div><strong>客户 A 应收逾期扩大</strong><small>发起智能体：应收智能体 · 责任人：应收管理组</small></div><span class="badge bad">审批人</span></div><div class="list-row"><div><strong>供应商付款建议 #PAY-250124</strong><small>付款智能体 · 高风险动作</small></div><span class="badge bad">已阻断</span></div></div></div></article></section>
        <section class="pane" data-pane-panel="actions"><div class="page-head"><div><div class="eyebrow">M10 · 动作下发</div><h1>POMS 动作</h1><p class="subtitle">财经建议进入待办与动作，执行反馈回流 FAC 进行验证。</p></div><div class="head-right"><button class="button primary" data-action="action">创建示例动作</button></div></div><article class="panel"><div class="panel-head"><div><h2>动作下发队列</h2><p>决策 → 动作 → 执行反馈</p></div><span class="badge good">12 个进行中</span></div><div class="panel-body"><div class="list"><div class="list-row"><div><strong>确认客户 A 回款计划</strong><small>POMS-AR-250124 · 责任人：应收管理组 · 截止：2025-01-27</small></div><span class="badge blue">进行中</span></div><div class="list-row"><div><strong>复核订单 B 成本构成</strong><small>POMS-OFA-250124 · 责任人：订单财经组 · 需要证据</small></div><span class="badge warn">待办</span></div><div class="list-row"><div><strong>确认制造费用预算偏差</strong><small>POMS-BUDGET-250124 · 责任人：预算管理组</small></div><span class="badge good">已确认</span></div></div></div></article></section>
        <section class="pane" data-pane-panel="evidence"><div class="page-head"><div><div class="eyebrow">M02 · 证据与验证</div><h1>证据</h1><p class="subtitle">每个正式财经结果都可以回钻到计算快照、规则与来源对象。</p></div><div class="head-right"><button class="button" data-action="refresh">刷新证据</button><span class="badge good">100% 可追溯</span></div></div><article class="panel"><div class="panel-head"><div><h2>证据链</h2><p>结果 → 快照 → 规则 → 来源 → 审计</p></div></div><div class="panel-body"><div class="activity"><div class="activity-row"><span class="activity-time">10:05:13.284</span><code>verify.finance_result</code><p>订单毛利结果 V2 验证完成，证据覆盖率 100%。</p></div><div class="activity-row"><span class="activity-time">10:05:13.018</span><code>m01.decision.approved</code><p>订单 B 风险决策案例已进入人工复核，智能体未越权验证。</p></div><div class="activity-row"><span class="activity-time">10:05:12.671</span><code>fac.ofa.snapshot</code><p>ORD-1001 V2 绑定 BOM-1001、PRICE-1001 修订版 2、规则 v1。</p></div><div class="activity-row"><span class="activity-time">10:05:12.402</span><code>edp.event.ack</code><p>CRM 报价重算事件已完成幂等消费，事件可安全回放。</p></div></div></div></article></section>
        <section class="panel" style="margin-top:17px" id="integration-details"><div class="panel-head"><div><h2>跨模块联调详情</h2><p>完整 FAC 工作台投影：注册、决策、动作、验证与回证均来自同一条关联链。</p></div><span class="badge blue">中文演示数据</span></div><div class="panel-body"><div class="projection-grid"><div><div class="subtle-label">M13 Registry 沙箱</div><div class="projection-list" id="agent-registry-list" style="margin-top:8px"></div></div><div><div class="subtle-label">M01 DecisionCase</div><div class="projection-list" id="decision-case-list" style="margin-top:8px"></div></div><div><div class="subtle-label">M10 POMS Action</div><div class="projection-list" id="poms-action-list" style="margin-top:8px"></div></div></div><div class="projection-row" id="verify-summary" style="margin-top:10px"><div><strong>FAC Verify → EBMS Result</strong><small>证据覆盖率、价值台账、执行反馈回流</small></div><div class="right"><span class="badge warn" id="verify-status">待验证</span><small id="verify-ledger">Value Ledger：待生成</small></div></div></div></section>
      </main>
    </section>
  </div>
  <script>
    const qs = (selector, root = document) => root.querySelector(selector); const qsa = (selector, root = document) => [...root.querySelectorAll(selector)];
    const toast = (message) => { const element = qs("#toast"); element.textContent = message; element.classList.add("show"); window.clearTimeout(window.facToastTimer); window.facToastTimer = window.setTimeout(() => element.classList.remove("show"), 2500); };
    const api = async (path, options = {}) => { const response = await fetch(path, {headers:{"Content-Type":"application/json"}, ...options}); const payload = await response.json(); if (!response.ok) throw new Error(payload.detail || `HTTP ${response.status}`); return payload; };
    const setPane = (name) => { qsa(".nav button[data-pane]").forEach((button) => { const active = button.dataset.pane === name; button.classList.toggle("active", active); if (active) button.setAttribute("aria-current", "page"); else button.removeAttribute("aria-current"); }); qsa(".pane").forEach((pane) => pane.classList.toggle("active", pane.dataset.panePanel === name)); window.scrollTo({top:0, behavior:"smooth"}); };
    qsa(".nav button[data-pane]").forEach((button) => button.addEventListener("click", () => setPane(button.dataset.pane))); qsa("[data-pane-link]").forEach((button) => button.addEventListener("click", () => setPane(button.dataset.paneLink)));
    const navMore = document.querySelector("[data-nav-more]"); const navMoreToggle = document.querySelector("[data-nav-more-toggle]");
    navMoreToggle?.addEventListener("click", () => { const expanded = !navMore.classList.contains("expanded"); navMore.classList.toggle("expanded", expanded); navMoreToggle.setAttribute("aria-expanded", String(expanded)); });
    qsa("[data-action='refresh']").forEach((button) => button.addEventListener("click", () => toast("投影、事件与证据状态已刷新"))); qsa("[data-action='action']").forEach((button) => button.addEventListener("click", () => { button.textContent = "已创建动作"; toast("POMS 动作已创建，等待执行反馈"); }));
    const statusLabels = {WAITING:"待运行", WAITING_EXTERNAL:"待外部处理", WAITING_EVIDENCE:"待验证", READY:"可调度", COMPLETED:"已完成", APPROVED:"已批准", BLOCKED:"已阻断", GUARDED:"受保护", VERIFIED:"已验证", CONSUMED:"已消费", PROCESSED:"已处理", ACKED:"已确认", REVIEW:"待复核", PENDING:"待决策", ALLOW:"允许", DENY:"拒绝"};
    const statusClass = (status) => ["COMPLETED","APPROVED","VERIFIED","CONSUMED","PROCESSED","ACKED"].includes(status) ? "good" : ["BLOCKED","DENY","GUARDED"].includes(status) ? "bad" : ["READY","WAITING","REVIEW","PENDING"].includes(status) ? "warn" : "blue";
    const statusText = (status) => statusLabels[status] || status;
    const escapeHtml = (value) => String(value ?? "").replace(/[&<>\"']/g, (character) => ({"&":"&amp;","<":"&lt;",">":"&gt;",'\"':"&quot;", "'":"&#39;"}[character]));
    const eventTypeText = (value) => ({QuoteRecalculationRequired:"报价重算事件", BOMReleased:"BOM 已发布", MarginRiskDetected:"毛利风险已识别"}[value] || value);
    const renderIntegration = (state) => {
      qs("#integration-correlation").textContent = state.correlation_id;
      qs("#integration-idempotency").textContent = state.idempotency_enabled ? "已启用" : "未启用";
      qs("#integration-mode").textContent = state.mode === "LOCAL_SANDBOX" ? "本地沙箱投影" : state.mode;
      qs("#integration-verify").textContent = statusText(state.verify.status);
      qs("#integration-evidence").textContent = `证据覆盖率 ${state.verify.evidence_coverage}% · EBMS ${statusText(state.ebms_status)}`;
      qs("#integration-stage-list").innerHTML = state.stages.map((stage) => `<div class="projection-row"><div><strong>${escapeHtml(stage.module)} · ${escapeHtml(stage.name)}</strong><small>${escapeHtml(stage.mode)} · 输入 ${stage.input_refs.length} 项 · 输出 ${stage.output_refs.length} 项</small></div><div class="right"><span class="badge ${statusClass(stage.status)}">${statusText(stage.status)}</span></div></div>`).join("");
      qs("#integration-event-list").innerHTML = state.event_ledger.map((event) => `<tr><td><code>${escapeHtml(event.event_id)}</code></td><td>${escapeHtml(eventTypeText(event.event_type))}</td><td>${escapeHtml(event.source)}</td><td>${escapeHtml(event.target)}</td><td><code>${escapeHtml(event.correlation_id)}</code></td><td><code>${escapeHtml(event.idempotency_key)}</code></td><td><span class="badge ${statusClass(event.status)}">${statusText(event.status)}</span></td></tr>`).join("");
      qs("#agent-registry-list").innerHTML = state.agents.map((agent) => `<div class="projection-row"><div><strong>${escapeHtml(agent.name)}</strong><small>${escapeHtml(agent.capabilities.join(" · "))} · ${escapeHtml(agent.action_level)} · ${escapeHtml(agent.source)}</small></div><div class="right"><span class="badge ${statusClass(agent.status)}">${agent.dispatchable ? "可调度" : statusText(agent.status)}</span></div></div>`).join("");
      const agentCount = qs("#agent-count"); if (agentCount) agentCount.textContent = `${state.agents.filter((agent) => agent.dispatchable).length} / ${state.agents.length} 可调度`;
      qs("#decision-case-list").innerHTML = state.decision_cases.map((item) => `<div class="projection-row"><div><strong>${escapeHtml(item.title)}</strong><small>${escapeHtml(item.case_id)} · ${escapeHtml(item.maker)} → ${escapeHtml(item.checker)} → ${escapeHtml(item.approver)}</small></div><div class="right"><span class="badge ${statusClass(item.status)}">${statusText(item.status)}</span><small>${statusText(item.decision)}</small></div></div>`).join("");
      qs("#poms-action-list").innerHTML = state.actions.map((item) => `<div class="projection-row"><div><strong>${escapeHtml(item.title)}</strong><small>${escapeHtml(item.action_id)} · ${escapeHtml(item.owner)} · 截止 ${escapeHtml(item.due_date)} · ${escapeHtml(item.feedback)}</small></div><div class="right"><span class="badge ${statusClass(item.status)}">${statusText(item.status)}</span></div></div>`).join("");
      qs("#verify-status").textContent = statusText(state.verify.status);
      qs("#verify-status").className = `badge ${statusClass(state.verify.status)}`;
      qs("#verify-ledger").textContent = `Value Ledger：${state.verify.value_ledger_id} · ${state.verify.roi_value}`;
      const nodeByModule = {"M02 EDP":"edp", "M09 FAC":"fac", "M13 Agent":"agent", "M01 Guard":"guard", "M10 POMS":"poms", "FAC Verify":"verify"};
      state.stages.forEach((stage) => markNode(nodeByModule[stage.module], stage.status === "COMPLETED" ? "done" : stage.status === "READY" ? "running" : "idle"));
    };
    const refreshIntegration = async () => { try { renderIntegration(await api("/api/v1/demo/integration")); } catch (error) { if (!String(error.message).includes("404")) toast(`状态刷新失败：${error.message}`); } };
    let latestRequest = {order_id:"ORD-1001", price_revision:2, event_id:"demo-event-v2", idempotency_key:"demo-key-v2", trigger_type:"QuoteRecalculationRequired", reason:"MaterialPriceRevision", actor:"demo-user"};
    const markNode = (name, status) => { const node = qs(`[data-node="${name}"]`); if (!node) return; node.classList.remove("running"); node.classList.toggle("done", status === "done"); const label = qs(".node-status span", node); const dot = qs(".node-status i", node); if (status === "done") { label.textContent = "已完成"; dot.style.background = "var(--green)"; } else if (status === "running") { node.classList.add("running"); label.textContent = "处理中"; dot.style.background = "var(--amber)"; } };
    const markRunbook = (step, done) => { const row = qs(`[data-step="${step}"]`); if (row) row.classList.toggle("done", done); };
    const runChain = async () => { const button = qs("#run"); button.disabled = true; button.textContent = "联调中…"; qs("#run-state").textContent = "A1 · 运行中"; qs("#trace-badge").textContent = "运行中"; markNode("source", "running"); try { await api("/api/v1/demo/reset", {method:"POST"}); markNode("source", "done"); markNode("edp", "running"); markRunbook(1, true); qs("#trace-1").textContent = "订单 / 物料清单 / 价格投影已进入 EDP"; const first = {...latestRequest, price_revision:1, event_id:"demo-event-v1", idempotency_key:"demo-key-v1", reason:"Initial quote"}; await api("/api/v1/demo/events/quote-recalculation", {method:"POST", body:JSON.stringify(first)}); markNode("edp", "done"); markNode("fac", "running"); markRunbook(2, true); qs("#trace-2").textContent = "计算 V1 46.00 CNY 已持久化"; const result = await api("/api/v1/demo/events/quote-recalculation", {method:"POST", body:JSON.stringify(latestRequest)}); markNode("fac", "done"); markNode("agent", "done"); markNode("guard", "done"); markNode("poms", "done"); markNode("verify", "done"); markRunbook(3, true); markRunbook(4, true); qsa(".arrow").forEach((arrow) => arrow.classList.add("done")); qs("#trace-3").textContent = "智能体建议已通过 M01 防护策略"; qs("#trace-4").textContent = `财经结果 V${result.result.version} 已通过证据验证`; qs("#ledger-status").textContent = "已处理"; qs("#ledger-status").className = "badge good"; qs("#trace-badge").textContent = "已验证"; qs("#run-state").textContent = `A1 · 结果 V${result.result.version}`; qs("#system-status").textContent = "链路已验证"; await refreshIntegration(); toast("FAC 联调完成：EDP → OFA V1/V2 → 智能体 → 防护 → POMS → 验证"); } catch (error) { qs("#run-state").textContent = "A0 · 出错"; qs("#trace-badge").textContent = "出错"; toast(`联调失败：${error.message}`); } finally { button.disabled = false; button.textContent = "运行联调演示"; } };
    const replay = async () => { try { const result = await api("/api/v1/demo/replay", {method:"POST", body:JSON.stringify(latestRequest)}); await refreshIntegration(); toast(result.replayed ? "回放已接受 · 未重复生成财经事实" : "事件已处理"); qs("#ledger-status").textContent = "可安全回放"; qs("#ledger-status").className = "badge blue"; } catch (error) { toast(`回放失败：${error.message}`); } };
    qs("#run").addEventListener("click", runChain); qs("#replay").addEventListener("click", replay); qs("#run-events").addEventListener("click", runChain); qs("#run-results").addEventListener("click", runChain); refreshIntegration();
  </script>
</body>
</html>'''
    replacements = {
        "本地联调沙箱": "正式运行环境",
        "租户：demo-tenant": "租户：当前租户",
        "M09 · 联调控制台": "M09 · 财经工作台",
        "财经结果": "结果与证据",
        "M09 工作台": "规则与期间 · M09 工作台",
        "运行联调演示": "计算订单",
        "重放最近事件": "刷新状态",
        "真实系统联调主干": "订单财经分析主干",
        "关联编号：FAC-DEMO-2025-01": "订单范围：当前租户",
        "FAC-DEMO-2025-01": "当前租户订单",
        "完整联调投影": "正式业务状态",
        "本地沙箱": "待接入",
        "运行示例链路": "计算订单",
        "运行 OFA 计算": "计算订单",
        "中文演示数据": "正式业务状态",
        "M13 Registry 沙箱": "M13 智能体注册",
        "2,418": "待接入",
        "4 / 5": "待接入",
        "12</strong><small>进行中动作": "待接入</strong><small>进行中动作",
        "100%</strong><small>高风险动作必须审批": "待验证</strong><small>高风险动作必须审批",
        "/demo/fac": "/fac",
        "/api/v1/demo/": "/api/v1/fac/",
        "demo-event-v1": "event-v1",
        "demo-margin-risk-v2": "margin-risk-v1",
        "demo-key-v1": "event-key-v1",
        "demo-event-v2": "event-v2",
        "demo-key-v2": "event-key-v2",
        "demo-user": "fac-user",
        "已验证链路": "待验证",
        "证据覆盖率</label><strong>100%</strong>": "证据覆盖率</label><strong>待验证</strong>",
        "100% 可追溯": "待验证",
        "46.00 CNY": "待计算",
        "52.00 CNY": "待计算",
        "计算快照已冻结": "需先计算订单",
        "物料价格修订版 2": "等待 EDP 价格输入",
        "Value Ledger：待生成": "价值台账：待生成",
        "result:plan:v2": "<span id=\"result-id\">待生成</span>",
        "订单毛利结果 · ORD-1001": "待生成订单财经结果",
        "PRICE-1001 · 修订版 2 · 已挂接证据": "等待 EDP 价格引用",
        "订单毛利结果 V2 验证完成，证据覆盖率 100%。": "结果生成后执行证据验证，当前待验证。",
        "ORD-1001 V2 绑定 BOM-1001、PRICE-1001 修订版 2、规则 v1。": "结果生成后展示冻结引用与证据状态。",
        "打开 OFA 明细": "查看结果明细",
        "创建示例动作": "查看待外部处理",
        "POMS 动作已创建，等待执行反馈": "暂无外部处理请求，当前状态：待外部处理",
        "refreshIntegration();": "",
    }
    for old, new in replacements.items():
        html = html.replace(old, new)
    front_css = r'''
<style>
  .front-shell { padding: 32px 0 56px; }
  .front-head { display:flex; align-items:flex-start; justify-content:space-between; gap:24px; margin-bottom:22px; }
  .front-head h1 { margin:4px 0 7px; font-size:34px; letter-spacing:-.03em; }
  .front-head p { margin:0; color:var(--muted); font-size:14px; }
  .front-kicker { color:#67c7ff; font-size:12px; font-weight:700; letter-spacing:.1em; text-transform:uppercase; }
  .front-system-link { color:#67c7ff; cursor:pointer; font-size:13px; padding-top:11px; white-space:nowrap; }
  .front-panel { background:linear-gradient(145deg,#102b43,#0d1e31); border:1px solid #24465e; border-radius:10px; box-shadow:0 14px 40px rgba(0,0,0,.18); }
  .front-orders { padding:18px 20px 12px; }
  .front-toolbar { display:flex; justify-content:space-between; align-items:center; gap:14px; margin-bottom:13px; }
  .front-toolbar h2, .front-analysis h2, .front-review-panel h2, .front-bottom h2 { margin:0; font-size:18px; }
  .front-count { color:var(--muted); font-size:12px; }
  .front-table { display:grid; gap:2px; }
  .front-table-head, .front-order-row { display:grid; grid-template-columns:1.1fr 1.35fr 1fr 1fr 1fr .8fr .8fr; align-items:center; gap:12px; }
  .front-table-head { padding:0 12px 8px; color:#7f9bb2; font-size:11px; }
  .front-order-row { min-height:54px; padding:9px 12px; color:#dbeaf5; border-top:1px solid rgba(103,160,196,.13); cursor:pointer; transition:background .18s, border .18s; }
  .front-order-row:hover, .front-order-row.selected { background:rgba(66,163,226,.12); border-color:#2f8dc5; }
  .front-order-row strong { font-size:13px; }
  .front-order-row small { display:block; color:var(--muted); margin-top:3px; font-size:11px; }
  .front-number { text-align:right; font-variant-numeric:tabular-nums; }
  .front-status { justify-self:start; padding:4px 8px; border-radius:999px; background:rgba(91,185,255,.13); color:#7fd0ff; font-size:11px; }
  .front-status.warn { background:rgba(242,185,109,.13); color:#f2c078; }
  .front-status.good { background:rgba(105,223,182,.13); color:#75e4bd; }
  .front-grid { display:grid; grid-template-columns:minmax(0,1.65fr) minmax(280px,.75fr); gap:17px; margin-top:17px; }
  .front-analysis, .front-review-panel { padding:22px; }
  .front-analysis-head { display:flex; align-items:flex-start; justify-content:space-between; gap:14px; }
  .front-analysis h2 { font-size:22px; }
  .front-meta { color:var(--muted); font-size:12px; margin-top:7px; }
  .front-state { color:#7fd0ff; font-size:12px; white-space:nowrap; }
  .front-metrics { display:grid; grid-template-columns:repeat(3,1fr); gap:11px; margin-top:20px; }
  .front-metric { padding:15px; border:1px solid #2a526c; border-radius:8px; background:rgba(8,20,33,.38); }
  .front-metric label { display:block; color:#9db4c5; font-size:11px; }
  .front-metric strong { display:block; margin-top:8px; font-size:24px; letter-spacing:-.03em; }
  .front-metric em { display:block; margin-top:5px; color:#79dfbd; font-size:11px; font-style:normal; }
  .front-metric.cost strong { color:#f5ca83; }
  .front-metric.margin { border-color:#2b7666; background:rgba(24,89,73,.16); }
  .front-metric.margin strong { color:#64e1b5; }
  .front-actions { display:flex; gap:11px; margin-top:20px; }
  .front-actions .button { min-width:180px; }
  .front-hint { margin:14px 0 0; color:#8ea8bb; font-size:12px; }
  .front-review-panel { min-height:265px; }
  .front-review-head { display:flex; justify-content:space-between; align-items:center; gap:12px; }
  .front-timeline { margin-top:22px; border-left:1px solid #2e566d; padding-left:18px; display:grid; gap:17px; }
  .front-step { position:relative; }
  .front-step:before { content:""; position:absolute; left:-24px; top:2px; width:9px; height:9px; border-radius:50%; background:#29475b; border:2px solid #0d1e31; }
  .front-step.active:before { background:#54b8f5; box-shadow:0 0 0 4px rgba(84,184,245,.13); }
  .front-step.done:before { background:#68dfb6; }
  .front-step strong { display:block; font-size:13px; }
  .front-step small { display:block; margin-top:4px; color:var(--muted); font-size:11px; line-height:1.5; }
  .front-bottom { display:grid; grid-template-columns:1.1fr .9fr; gap:17px; margin-top:17px; }
  .front-bottom > article { padding:20px; }
  .front-bottom-head { display:flex; justify-content:space-between; align-items:center; gap:12px; }
  .front-coverage { display:flex; align-items:center; gap:15px; margin-top:18px; }
  .front-coverage strong { color:#f2c078; font-size:28px; }
  .front-progress { flex:1; height:8px; overflow:hidden; border-radius:99px; background:#2c465a; }
  .front-progress i { display:block; height:100%; width:0; border-radius:99px; background:#f2b96d; transition:width .25s; }
  .front-coverage small { color:var(--muted); white-space:nowrap; }
  .front-evidence-list, .front-external-list { display:grid; gap:8px; margin-top:16px; }
  .front-evidence-row, .front-external-row { display:flex; justify-content:space-between; gap:16px; padding:10px 0; border-top:1px solid rgba(103,160,196,.13); font-size:12px; }
  .front-evidence-row span, .front-external-row span { color:#c9dce8; }
  .front-evidence-row small, .front-external-row small { color:#f2c078; text-align:right; }
  .front-empty { padding:24px 12px; color:var(--muted); text-align:center; }
  .nav-more { margin-top:8px; padding-top:8px; border-top:1px solid rgba(103,160,196,.14); }
  .nav-more-toggle { color:#8ea8bb; }
  .nav-more-toggle:hover, .nav-more.expanded .nav-more-toggle { color:#dbeaf5; background:rgba(66,163,226,.1); }
  .nav-secondary { display:none; gap:4px; margin-top:4px; }
  .nav-more.expanded .nav-secondary { display:grid; }
  .nav-secondary button { color:#8ea8bb; }
  .settings-grid { display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:17px; margin-top:17px; }
  .settings-card { padding:20px; }
  .settings-card h2 { margin:0; font-size:18px; }
  .settings-card > p { margin:7px 0 0; color:var(--muted); font-size:12px; }
  .settings-list { display:grid; gap:8px; margin-top:16px; }
  .settings-row { display:flex; align-items:center; justify-content:space-between; gap:16px; padding:11px 0; border-top:1px solid rgba(103,160,196,.13); }
  .settings-row strong { display:block; font-size:12px; }
  .settings-row small { display:block; margin-top:4px; color:var(--muted); font-size:11px; }
  .settings-note { margin-top:17px; padding:13px 15px; border:1px dashed #31566d; border-radius:8px; color:#9db4c5; font-size:12px; line-height:1.6; }
  #integration-details { display:none; }
  @media (max-width:900px) { .settings-grid { grid-template-columns:1fr; } }
  @media (max-width:900px) { .front-table-head, .front-order-row { grid-template-columns:1fr 1fr 1fr; } .front-table-head span:nth-child(n+4), .front-order-row > :nth-child(n+4) { display:none; } .front-grid, .front-bottom { grid-template-columns:1fr; } }
  @media (max-width:560px) { .front-shell { padding-top:20px; } .front-head { display:block; } .front-system-link { display:inline-block; margin-top:14px; } .front-metrics { grid-template-columns:1fr; } .front-actions { flex-direction:column; } .front-actions .button { width:100%; } .front-order-row { grid-template-columns:1fr 1fr; } .front-order-row > :nth-child(n+3) { display:none; } }
</style>
'''
    html = html.replace("</head>", front_css + "</head>")
    formal_script = r'''
  <script>
    const formalApi = async (path, options = {}) => {
      const response = await fetch(path, {headers:{"Content-Type":"application/json"}, ...options});
      const payload = await response.json();
      if (!response.ok) throw new Error(payload.detail || `HTTP ${response.status}`);
      return payload;
    };
    const replaceHandler = (selector, handler) => {
      const current = document.querySelector(selector);
      if (!current) return;
      const button = current.cloneNode(true);
      current.replaceWith(button);
      button.addEventListener("click", handler);
    };
    const formalState = {orders:[], rules:[], periods:[], events:[], externalRequests:[], result:null, evidence:null};
    const frontMoney = (value, currency = "CNY") => value === null || value === undefined || value === "" ? "待计算" : `${Number(value).toLocaleString("zh-CN", {minimumFractionDigits:2, maximumFractionDigits:2})} ${currency}`;
    const frontSales = (order) => {
      const payload = order?.payload || {};
      const quantity = Number(payload.quantity || 0);
      const unit = Number(payload.unit_price?.amount || 0);
      return quantity && unit ? {amount: quantity * unit, currency: payload.unit_price.currency || "CNY"} : null;
    };
    const mountSettingsPane = () => {
      const page = document.querySelector("main.page");
      if (!page || document.querySelector('[data-pane-panel="settings"]')) return;
      page.insertAdjacentHTML("beforeend", `<section class="pane" data-pane-panel="settings">
        <div class="page-head"><div><div class="eyebrow">M09 · 后台配置</div><h1>标准 / 设置 / 接口</h1><p class="subtitle">财经业务操作保持在前台；标准、参数和系统接口集中放在这里维护与查看。</p></div><div class="head-right"><span class="badge blue">后台配置区</span></div></div>
        <div class="settings-grid">
          <article class="panel settings-card"><h2>财经标准与规则</h2><p>版本化规则、来源字段和证据要求。</p><div class="settings-list" id="settings-rule-list"><div class="front-empty">正在加载规则…</div></div></article>
          <article class="panel settings-card"><h2>期间与运行设置</h2><p>本位币、期间状态和正式运行边界。</p><div class="settings-list" id="settings-period-list"><div class="front-empty">正在加载期间…</div></div></article>
          <article class="panel settings-card"><h2>系统接口</h2><p>外部系统接入状态和待接入边界。</p><div class="settings-list" id="settings-interface-list"></div></article>
          <article class="panel settings-card"><h2>当前运行配置</h2><p>仅展示当前租户的运行边界，不在前台业务流程中打扰操作。</p><div class="settings-list"><div class="settings-row"><div><strong>运行环境</strong><small>正式环境 · production</small></div><span class="badge good">已启用</span></div><div class="settings-row"><div><strong>Demo 模式</strong><small>正式入口不暴露演示接口</small></div><span class="badge good">已关闭</span></div><div class="settings-row"><div><strong>租户范围</strong><small>当前租户 · tenant-a</small></div><span class="badge blue">已隔离</span></div></div></article>
        </div><div class="settings-note">配置变更应通过正式审批和版本发布流程完成；当前页面先提供标准、设置和接口状态的集中查看入口。</div>
      </section>`);
    };
    const mountFrontOffice = () => {
      const pane = document.querySelector('[data-pane-panel="control"]');
      if (!pane) return;
      pane.innerHTML = `<div class="front-shell">
        <header class="front-head"><div><div class="front-kicker">M09 · 财经工作台</div><h1>订单财经分析</h1><p>完成订单的收入、成本、毛利测算与复核提报，证据与外部处理状态一并跟踪。</p></div><a class="front-system-link" id="front-system-link">系统详情 →</a></header>
        <section class="front-panel front-orders"><div class="front-toolbar"><h2>选择订单</h2><span class="front-count" id="front-order-count">待接入订单</span></div><div class="front-table"><div class="front-table-head"><span>订单编号</span><span>客户 / 产品</span><span>销售金额</span><span>计划成本</span><span>预计毛利</span><span>复核状态</span><span>证据覆盖</span></div><div id="front-order-list" class="front-table"><div class="front-empty">正在加载正式订单…</div></div></div></section>
        <section class="front-grid"><article class="front-panel front-analysis"><div class="front-analysis-head"><div><h2 id="front-analysis-title">选择订单后开始分析</h2><div id="front-analysis-meta" class="front-meta">订单、BOM、价格和汇率由 M02 EDP 提供</div></div><span class="front-state" id="front-analysis-state">待接入</span></div><div class="front-metrics"><div class="front-metric"><label>销售金额</label><strong id="front-sales">待选择</strong><em>订单收入</em></div><div class="front-metric cost"><label>计划成本</label><strong id="front-cost">待计算</strong><em id="front-cost-status">需先计算订单</em></div><div class="front-metric margin"><label>预计毛利</label><strong id="front-margin">待计算</strong><em id="front-margin-status">生成结果后展示</em></div></div><div class="front-actions"><button class="button primary" id="run">计算订单</button><button class="button" id="front-review">提交复核</button></div><p class="front-hint" id="front-hint">提示：请先计算订单生成最新财经结果，确认输入证据后再提交复核。</p></article><aside class="front-panel front-review-panel"><div class="front-review-head"><h2>复核状态</h2><span class="badge warn" id="front-review-badge">待计算</span></div><div class="front-timeline"><div class="front-step active" id="front-step-calculate"><strong>财经测算</strong><small>计算订单的收入、计划成本与预计毛利</small></div><div class="front-step" id="front-step-submit"><strong>提交复核</strong><small>提交财经结果与证据，等待复核</small></div><div class="front-step" id="front-step-review"><strong>复核中</strong><small>复核人员核对财经结果与证据</small></div><div class="front-step" id="front-step-done"><strong>复核完成</strong><small>确认结果并归档</small></div></div></aside></section>
        <section class="front-bottom"><article class="front-panel"><div class="front-bottom-head"><h2>证据覆盖率</h2><span class="badge warn" id="front-evidence-badge">待验证</span></div><div class="front-coverage"><strong id="front-evidence-coverage">0%</strong><div class="front-progress"><i id="front-evidence-progress"></i></div><small id="front-evidence-count">待生成结果</small></div><div class="front-evidence-list" id="front-evidence-list"><div class="front-empty">生成财经结果后展示证据状态</div></div></article><article class="front-panel"><div class="front-bottom-head"><h2>待外部处理</h2><span class="badge warn" id="front-external-count">0 项</span></div><div class="front-external-list" id="front-external-list"><div class="front-empty">暂无外部处理请求</div></div></article></section>
      </div>`;
      document.querySelector("#front-system-link")?.addEventListener("click", (event) => {
        const details = document.querySelector("#integration-details");
        if (!details) return;
        const open = details.style.display !== "block";
        details.style.display = open ? "block" : "none";
        event.currentTarget.textContent = open ? "收起系统详情 ↑" : "系统详情 →";
        if (open) details.scrollIntoView({behavior:"smooth", block:"start"});
      });
      document.querySelector("#front-review")?.addEventListener("click", () => toast(formalState.result ? "复核接口已预留，当前状态：待外部处理" : "请先计算订单生成财经结果"));
    };
    const renderFrontOffice = () => {
      const list = document.querySelector("#front-order-list");
      if (!list) return;
      const selected = formalState.orders.find((item) => item.order_id === formalState.selectedOrderId) || formalState.orders[0];
      formalState.selectedOrderId = selected?.order_id || null;
      const resultForSelected = formalState.result && formalState.result.result_id?.includes(selected?.order_id || "") ? formalState.result : null;
      document.querySelector("#front-order-count").textContent = formalState.orders.length ? `${formalState.orders.length} 个正式订单` : "待接入订单";
      list.innerHTML = formalState.orders.length ? formalState.orders.map((order) => {
        const sales = frontSales(order);
        const isSelected = order.order_id === selected?.order_id;
        const rowResult = isSelected ? resultForSelected : null;
        const cost = rowResult?.total_cost?.functional_amount;
        const margin = sales && cost ? sales.amount - Number(cost) : null;
        return `<div class="front-order-row ${isSelected ? "selected" : ""}" data-front-order="${escapeHtml(order.order_id)}"><div><strong>${escapeHtml(order.order_id)}</strong><small>${escapeHtml(order.payload?.order_date || "正式订单")}</small></div><div><strong>${escapeHtml(order.payload?.customer_id || "待接入客户")}</strong><small>${escapeHtml(order.payload?.product_id || "待接入产品")}</small></div><div class="front-number">${sales ? frontMoney(sales.amount, sales.currency) : "待接入"}</div><div class="front-number">${cost ? frontMoney(cost, rowResult.total_cost.functional_currency) : "待计算"}</div><div class="front-number">${margin === null ? "待计算" : frontMoney(margin, sales.currency)}</div><span class="front-status ${rowResult ? "good" : "warn"}">${rowResult ? "待复核" : "待计算"}</span><span class="front-status warn">${formalState.evidence?.evidence_coverage || 0}%</span></div>`;
      }).join("") : `<div class="front-empty">当前租户暂无订单，请先接入 M02 EDP。</div>`;
      document.querySelectorAll("[data-front-order]").forEach((row) => row.addEventListener("click", () => { formalState.selectedOrderId = row.dataset.frontOrder; renderFrontOffice(); }));
      const sales = frontSales(selected);
      const cost = resultForSelected?.total_cost;
      const margin = sales && cost ? sales.amount - Number(cost.functional_amount) : null;
      document.querySelector("#front-analysis-title").textContent = selected ? `订单分析：${selected.order_id}` : "选择订单后开始分析";
      document.querySelector("#front-analysis-meta").textContent = selected ? `客户：${selected.payload?.customer_id || "待接入"}　|　产品：${selected.payload?.product_id || "待接入"}　|　来源：${selected.source_system}` : "订单、BOM、价格和汇率由 M02 EDP 提供";
      document.querySelector("#front-analysis-state").textContent = resultForSelected ? `结果 V${resultForSelected.version}` : selected ? "待计算" : "待接入";
      document.querySelector("#front-sales").textContent = sales ? frontMoney(sales.amount, sales.currency) : "待选择";
      document.querySelector("#front-cost").textContent = cost ? frontMoney(cost.functional_amount, cost.functional_currency) : "待计算";
      document.querySelector("#front-cost-status").textContent = cost ? `结果状态：${resultForSelected.status}` : "需先计算订单";
      document.querySelector("#front-margin").textContent = margin === null ? "待计算" : frontMoney(margin, sales.currency);
      document.querySelector("#front-margin-status").textContent = margin === null ? "生成结果后展示" : `毛利率：${sales.amount ? ((margin / sales.amount) * 100).toFixed(2) : "0.00"}%`;
      document.querySelector("#front-review-badge").textContent = resultForSelected ? "待复核" : "待计算";
      document.querySelector("#front-review-badge").className = `badge ${resultForSelected ? "warn" : "blue"}`;
      document.querySelector("#front-hint").textContent = resultForSelected ? "结果已生成，证据仍需核验；外部复核接口接入后可提交复核。" : selected ? "提示：请先计算订单生成最新财经结果，确认输入证据后再提交复核。" : "提示：请先接入 M02 EDP 订单。";
      const coverage = formalState.evidence?.evidence_coverage || 0;
      document.querySelector("#front-evidence-coverage").textContent = `${coverage}%`;
      document.querySelector("#front-evidence-progress").style.width = `${coverage}%`;
      document.querySelector("#front-evidence-badge").textContent = formalState.evidence?.status === "VERIFIED" ? "已验证" : "待验证";
      document.querySelector("#front-evidence-count").textContent = formalState.evidence ? `${formalState.evidence.evidence_refs.length} 项证据引用` : "待生成结果";
      document.querySelector("#front-evidence-list").innerHTML = formalState.evidence ? `<div class="front-evidence-row"><span>财经结果</span><small>${escapeHtml(formalState.evidence.status)}</small></div><div class="front-evidence-row"><span>输入引用</span><small>${formalState.result?.evidence_refs?.length || 0} 项，待核验</small></div>` : `<div class="front-empty">生成财经结果后展示证据状态</div>`;
      const external = document.querySelector("#front-external-list");
      document.querySelector("#front-external-count").textContent = `${formalState.externalRequests.length} 项`;
      external.innerHTML = formalState.externalRequests.length ? formalState.externalRequests.slice(0,3).map((item) => `<div class="front-external-row"><span>${escapeHtml(item.request_type)}<small>${escapeHtml(item.target_system)}</small></span><small>${escapeHtml(item.status)}</small></div>`).join("") : `<div class="front-empty">暂无外部处理请求</div>`;
    };
    const setFormalWaiting = (message = "待接入 EDP 业务对象") => {
      const state = document.querySelector("#run-state");
      if (state) state.textContent = "A0 · 待接入";
      const trace = document.querySelector("#trace-badge");
      if (trace) trace.textContent = "待接入";
      const evidence = document.querySelector("#integration-evidence");
      if (evidence) evidence.textContent = "证据覆盖率 0% · 待外部处理";
      ["trace-1", "trace-2", "trace-3", "trace-4"].forEach((id) => {
        const node = document.querySelector(`#${id}`);
        if (node) node.textContent = message;
      });
    };
    const renderFormalCollections = () => {
      const order = formalState.orders[0];
      const correlation = document.querySelector("#integration-correlation");
      if (correlation) correlation.textContent = order ? order.order_id : "待接入订单";
      const eventList = document.querySelector("#integration-event-list");
      if (eventList) {
        eventList.innerHTML = formalState.events.length ? formalState.events.map((event) => `<tr><td><code>${escapeHtml(event.event_id)}</code></td><td>${escapeHtml(event.event_type || "财经计算事件")}</td><td>${escapeHtml(event.source_system)}</td><td>M09 FAC</td><td><code>${escapeHtml(event.object_id)}</code></td><td><code>${escapeHtml(event.idempotency_key)}</code></td><td><span class="badge warn">已记录</span></td></tr>`).join("") : `<tr><td colspan="7"><span class="badge warn">待接入事件</span></td></tr>`;
      }
      const summaryLedger = document.querySelector(".dashboard-grid table tbody");
      if (summaryLedger) summaryLedger.innerHTML = formalState.events.length ? formalState.events.slice(-3).map((event) => `<tr><td><code>${escapeHtml(event.event_id)}</code></td><td>${escapeHtml(event.source_system)}</td><td>M09 FAC</td><td><code>${escapeHtml(event.object_id)}</code></td><td><span class="badge warn" id="ledger-status">已记录</span></td></tr>`).join("") : `<tr><td colspan="5"><span class="badge warn" id="ledger-status">待接入事件</span></td></tr>`;
      const signalValues = document.querySelectorAll(".signal strong");
      if (signalValues.length >= 4) {
        signalValues[0].textContent = formalState.orders.length ? String(formalState.orders.length) : "待接入";
        signalValues[1].textContent = "待接入";
        signalValues[2].textContent = "待验证";
        signalValues[3].textContent = "待接入";
      }
      const stageList = document.querySelector("#integration-stage-list");
      if (stageList) stageList.innerHTML = `<div class="projection-row"><div><strong>M02 EDP · 订单对象</strong><small>${order ? "已接入当前租户订单" : "等待外部系统提供订单对象"}</small></div><div class="right"><span class="badge ${order ? "good" : "warn"}">${order ? "已接入" : "待接入"}</span></div></div><div class="projection-row"><div><strong>M09 FAC · 订单财经计算</strong><small>规则与期间冻结后生成版本化财经结果</small></div><div class="right"><span class="badge warn">待计算</span></div></div><div class="projection-row"><div><strong>外部系统回写</strong><small>${formalState.externalRequests.length ? "存在外部处理请求" : "暂无外部回写请求"}</small></div><div class="right"><span class="badge warn">待外部处理</span></div></div>`;
      const agents = document.querySelector("#agent-registry-list");
      if (agents) agents.innerHTML = `<div class="projection-row"><div><strong>M13 智能体注册</strong><small>接口已预留，等待注册中心接入</small></div><div class="right"><span class="badge warn">待接入</span></div></div>`;
      const decisions = document.querySelector("#decision-case-list");
      if (decisions) decisions.innerHTML = `<div class="projection-row"><div><strong>M01 决策案例</strong><small>财经结果生成后进入人工复核</small></div><div class="right"><span class="badge warn">待生成</span></div></div>`;
      const actions = document.querySelector("#poms-action-list");
      if (actions) actions.innerHTML = `<div class="projection-row"><div><strong>M10 POMS 动作</strong><small>外部动作接口已预留</small></div><div class="right"><span class="badge warn">待外部处理</span></div></div>`;
      const settingsRules = document.querySelector("#settings-rule-list");
      if (settingsRules) settingsRules.innerHTML = formalState.rules.length ? formalState.rules.map((rule) => `<div class="settings-row"><div><strong>${escapeHtml(rule.rule_name)} · ${escapeHtml(rule.rule_id)}</strong><small>版本 ${escapeHtml(rule.version)} · 生效 ${escapeHtml(rule.effective_from)} · ${rule.evidence_required ? "需要证据" : "无需证据"}</small></div><span class="badge ${statusClass(rule.status)}">${statusText(rule.status)}</span></div>`).join("") : `<div class="front-empty">暂无财经规则，请先接入规则注册表。</div>`;
      const settingsPeriods = document.querySelector("#settings-period-list");
      if (settingsPeriods) settingsPeriods.innerHTML = formalState.periods.length ? formalState.periods.map((period) => `<div class="settings-row"><div><strong>${escapeHtml(period.period_id)}</strong><small>本位币 ${escapeHtml(period.functional_currency)}${period.closed_at ? ` · 关闭于 ${escapeHtml(period.closed_at)}` : ""}</small></div><span class="badge ${statusClass(period.status)}">${statusText(period.status)}</span></div>`).join("") : `<div class="front-empty">暂无财经期间，请先配置期间。</div>`;
      const settingsInterfaces = document.querySelector("#settings-interface-list");
      if (settingsInterfaces) settingsInterfaces.innerHTML = `<div class="settings-row"><div><strong>M02 EDP</strong><small>订单、BOM、价格、汇率、证据</small></div><span class="badge ${formalState.orders.length ? "good" : "warn"}">${formalState.orders.length ? "已接入" : "待接入"}</span></div><div class="settings-row"><div><strong>M13 Agent</strong><small>智能体注册与能力查询</small></div><span class="badge warn">待接入</span></div><div class="settings-row"><div><strong>M01 Guard</strong><small>决策案例与职责分离</small></div><span class="badge warn">待接入</span></div><div class="settings-row"><div><strong>M10 POMS / EBMS</strong><small>动作执行、反馈和结果消费</small></div><span class="badge warn">待接入</span></div>`;
      setFormalWaiting();
      if (formalState.result) {
        const resultId = document.querySelector("#result-id"); if (resultId) resultId.textContent = formalState.result.result_id;
        const state = document.querySelector("#run-state"); if (state) state.textContent = `A1 · 结果 V${formalState.result.version}`;
        const trace = document.querySelector("#trace-badge"); if (trace) trace.textContent = "已生成";
        const traceResult = document.querySelector("#trace-2"); if (traceResult) traceResult.textContent = `财经结果 V${formalState.result.version} 已生成，等待证据验证`;
        const ledgerStatus = document.querySelector("#ledger-status"); if (ledgerStatus) { ledgerStatus.textContent = "已生成"; ledgerStatus.className = "badge warn"; }
        const amount = formalState.result.total_cost ? `${formalState.result.total_cost.functional_amount} ${formalState.result.total_cost.functional_currency}` : "待计算";
        const resultV1 = document.querySelector("#result-v1"); if (resultV1) resultV1.textContent = amount;
        const evidenceCard = document.querySelector("[data-pane-panel=\"results\"] .stat-card:nth-child(3) strong"); if (evidenceCard) evidenceCard.textContent = `${formalState.evidence?.evidence_coverage ?? 0}%`;
        const resultRows = document.querySelectorAll("[data-pane-panel=\"results\"] .list-row");
        if (resultRows[0]) { resultRows[0].querySelector("strong").textContent = `订单财经结果 · ${formalState.orders[0]?.order_id || "当前订单"}`; resultRows[0].querySelector("small").textContent = `版本 V${formalState.result.version} · 结果状态 ${formalState.result.status}`; }
        if (resultRows[2]) resultRows[2].querySelector("small").textContent = `冻结输入引用 ${formalState.result.evidence_refs.length} 项 · 证据 ${formalState.evidence?.status || "待查询"}`;
        const evidenceActivity = document.querySelector("[data-pane-panel=\"evidence\"] .activity");
        if (evidenceActivity) evidenceActivity.innerHTML = `<div class="activity-row"><span class="activity-time">FAC</span><code>finance.result</code><p>结果 ${escapeHtml(formalState.result.result_id)} 已生成，证据状态：${escapeHtml(formalState.evidence?.status || "WAITING_EVIDENCE")}，覆盖率 ${formalState.evidence?.evidence_coverage ?? 0}%。</p></div>`;
      }
      renderFrontOffice();
    };
    const loadFormalState = async () => {
      try {
        const [orders, rules, periods, events, externalRequests] = await Promise.all([
          formalApi("/api/v1/fac/orders"),
          formalApi("/api/v1/fac/rules"),
          formalApi("/api/v1/fac/periods"),
          formalApi("/api/v1/fac/events"),
          formalApi("/api/v1/fac/external-requests"),
        ]);
        Object.assign(formalState, {orders, rules, periods, events, externalRequests});
        formalState.selectedOrderId = formalState.selectedOrderId || orders[0]?.order_id || null;
        formalState.result = null;
        formalState.evidence = null;
        const selected = orders.find((item) => item.order_id === formalState.selectedOrderId) || orders[0];
        if (selected) {
          try {
            formalState.result = await formalApi(`/api/v1/fac/orders/${encodeURIComponent(selected.order_id)}/financial-result?tenant_id=${encodeURIComponent(selected.tenant_id)}`);
            formalState.evidence = await formalApi(`/api/v1/fac/results/${encodeURIComponent(formalState.result.result_id)}/evidence?tenant_id=${encodeURIComponent(selected.tenant_id)}`);
          } catch (error) {
            if (!String(error.message).includes("404")) throw error;
          }
        }
        renderFormalCollections();
      } catch (error) {
        setFormalWaiting(`正式数据加载失败：${error.message}`);
        toast(`正式数据加载失败：${error.message}`);
      }
    };
    const calculateFormalOrder = async () => {
      const order = formalState.orders.find((item) => item.order_id === formalState.selectedOrderId) || formalState.orders[0];
      if (!order) { setFormalWaiting("暂无 EDP 订单，当前状态：待接入"); toast("暂无可计算订单：请先接入 M02 EDP"); return; }
      const refs = order.input_refs || [{object_type:"Order", object_id:order.order_id, source_system:order.source_system, revision:order.revision}];
      const body = {tenant_id:order.tenant_id, order_id:order.order_id, period_id:formalState.periods[0]?.period_id || "未配置期间", rule_id:formalState.rules[0]?.rule_id || "OFA_PLAN_COST", rule_version:formalState.rules[0]?.version || "v1", input_refs:refs, actor:"fac-user", idempotency_key:`fac-ui-${order.order_id}-${Date.now()}`, reason:"正式工作台订单财经计算"};
      try {
        const button = document.querySelector("#run"); if (button) { button.disabled = true; button.textContent = "计算中…"; }
        const result = await formalApi(`/api/v1/fac/orders/${encodeURIComponent(order.order_id)}/calculations`, {method:"POST", body:JSON.stringify(body)});
        formalState.result = result.result;
        formalState.evidence = await formalApi(`/api/v1/fac/results/${encodeURIComponent(result.result.result_id)}/evidence`);
        const resultId = document.querySelector("#result-id"); if (resultId) resultId.textContent = result.result.result_id;
        document.querySelector("#run-state").textContent = `A1 · 结果 V${result.result.version}`;
        document.querySelector("#trace-badge").textContent = "已生成";
        document.querySelector("#trace-2").textContent = `财经结果 V${result.result.version} 已生成，等待证据验证`;
        document.querySelector("#ledger-status").textContent = "已生成";
        document.querySelector("#ledger-status").className = "badge warn";
        toast("订单财经结果已生成，证据状态仍需核验");
        await loadFormalState();
        window.setTimeout(() => {
          const state = document.querySelector("#run-state"); if (state) state.textContent = `A1 · 结果 V${result.result.version}`;
          const trace = document.querySelector("#trace-badge"); if (trace) trace.textContent = "已生成";
          const traceResult = document.querySelector("#trace-2"); if (traceResult) traceResult.textContent = `财经结果 V${result.result.version} 已生成，等待证据验证`;
          const ledgerStatus = document.querySelector("#ledger-status"); if (ledgerStatus) { ledgerStatus.textContent = "已生成"; ledgerStatus.className = "badge warn"; }
        }, 0);
      } catch (error) { toast(`订单计算失败：${error.message}`); }
      finally { const button = document.querySelector("#run"); if (button) { button.disabled = false; button.textContent = "计算订单"; } }
    };
    const showFormalEvidence = async () => {
      const result = document.querySelector("#result-id")?.textContent?.trim();
      if (!result || result === "待生成") { toast("暂无财经结果，先计算订单"); return; }
      try { const evidence = await formalApi(`/api/v1/fac/results/${encodeURIComponent(result)}/evidence`); toast(`证据状态：${evidence.status} · 覆盖率 ${evidence.evidence_coverage}%`); } catch (error) { toast(`证据查询失败：${error.message}`); }
    };
    replaceHandler("#run", calculateFormalOrder);
    replaceHandler("#run-events", loadFormalState);
    replaceHandler("#run-results", calculateFormalOrder);
    replaceHandler("#replay", loadFormalState);
    document.querySelectorAll("[data-action=\"action\"]").forEach((current) => {
      const button = current.cloneNode(true);
      current.replaceWith(button);
      button.addEventListener("click", async () => {
        try {
          const requests = await formalApi("/api/v1/fac/external-requests");
          document.querySelector("[data-pane=\"actions\"]")?.click();
          toast(requests.length ? `待外部处理：${requests.length} 条` : "暂无外部处理请求，当前状态：待外部处理");
        } catch (error) { toast(`外部处理状态查询失败：${error.message}`); }
      });
    });
    document.querySelectorAll("[data-action=\"refresh\"]").forEach((current) => {
      const button = current.cloneNode(true);
      current.replaceWith(button);
      button.addEventListener("click", loadFormalState);
    });
    const frontNavCopy = {control:"订单分析", events:"系统详情", results:"财经结果", agents:"智能体协同", guards:"复核管理", actions:"待外部处理", evidence:"证据管理", settings:"标准 / 设置 / 接口"};
    document.querySelectorAll(".nav button[data-pane]").forEach((button) => {
      const label = button.querySelector("span:last-child");
      if (label && frontNavCopy[button.dataset.pane]) label.textContent = frontNavCopy[button.dataset.pane];
    });
    const brandSubline = document.querySelector(".brand small");
    if (brandSubline) brandSubline.textContent = "M09 · 财经自治中心";
    mountSettingsPane();
    mountFrontOffice();
    renderFrontOffice();
    loadFormalState();
  </script>
'''
    return html.replace("</body>", formal_script + "</body>")
