"""Browser workbench for the complete local FAC product demo."""


def render_fac_page() -> str:
    """Return a self-contained FAC workbench for local demonstrations."""
    return r'''<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>FAC · 财经自治中心</title>
  <style>
    :root { --ink:#132536; --muted:#71808b; --canvas:#f4f3ef; --surface:#fffefa;
      --line:#dfe2dc; --navy:#142737; --mint:#bdebd0; --green:#1f895a;
      --green-dark:#176c47; --amber:#d49a2f; --amber-bg:#fff4d9; --red:#c85e58;
      --red-bg:#ffe7e2; --shadow:0 16px 38px rgba(20,39,55,.07); }
    * { box-sizing:border-box; }
    body { margin:0; color:var(--ink); background:var(--canvas); font:14px/1.5 Inter,
      ui-sans-serif, system-ui, -apple-system, "Segoe UI", sans-serif; }
    button, select { font:inherit; }
    button { border:0; cursor:pointer; }
    .app { min-height:100vh; display:grid; grid-template-columns:236px minmax(0,1fr); }
    .sidebar { color:#eef5f2; background:var(--navy); padding:25px 16px 22px; display:flex; flex-direction:column; }
    .brand { display:flex; gap:12px; align-items:center; padding:0 12px 25px; border-bottom:1px solid rgba(255,255,255,.11); }
    .brand-mark { width:40px; height:40px; display:grid; place-items:center; color:var(--navy); background:var(--mint); border-radius:11px; font-weight:850; font-size:20px; }
    .brand strong { display:block; font-size:20px; line-height:1; letter-spacing:.01em; }
    .brand small { display:block; color:#9fb5b6; margin-top:5px; font-size:10px; letter-spacing:.11em; }
    .workspace { color:#a9bec0; padding:23px 12px 9px; font-size:11px; letter-spacing:.11em; text-transform:uppercase; }
    .nav { display:grid; gap:5px; }
    .nav button { display:flex; align-items:center; gap:12px; width:100%; padding:12px 13px; color:#d6e3df; background:transparent; border-radius:10px; text-align:left; transition:background .18s ease, transform .18s ease, color .18s ease; }
    .nav button:hover { color:#fff; background:rgba(255,255,255,.08); transform:translateX(2px); }
    .nav button.active { color:var(--navy); background:var(--mint); font-weight:760; }
    .nav-icon { width:18px; text-align:center; font-size:16px; }
    .sidebar-footer { margin-top:auto; padding:16px 12px 0; color:#a9bec0; border-top:1px solid rgba(255,255,255,.11); font-size:12px; }
    .sidebar-footer strong { display:block; color:#eef5f2; margin-bottom:3px; }
    .main { min-width:0; }
    .topbar { height:72px; padding:0 38px; display:flex; align-items:center; justify-content:space-between; background:rgba(255,254,250,.88); border-bottom:1px solid var(--line); backdrop-filter:blur(12px); position:sticky; top:0; z-index:5; }
    .topbar-left { display:flex; align-items:center; gap:12px; }
    .factory-icon { width:29px; height:29px; display:grid; place-items:center; color:var(--green-dark); border:1px solid #a8d4bc; border-radius:8px; }
    .topbar-left strong { font-size:16px; }
    .topbar-right { display:flex; align-items:center; gap:18px; color:var(--muted); }
    .data-status { display:flex; gap:7px; align-items:center; white-space:nowrap; }
    .dot { width:8px; height:8px; background:#2ca96a; border-radius:50%; box-shadow:0 0 0 4px #d9f1e2; }
    .period { padding:8px 10px; color:var(--ink); background:transparent; border:1px solid var(--line); border-radius:8px; }
    .user { width:31px; height:31px; display:grid; place-items:center; color:var(--green-dark); background:#d8f0df; border-radius:50%; font-weight:800; }
    .page { width:min(1450px, calc(100% - 76px)); margin:0 auto; padding:35px 0 60px; }
    .page-head { display:flex; align-items:end; justify-content:space-between; gap:24px; margin-bottom:26px; }
    h1,h2,h3,p { margin:0; }
    h1 { font-size:clamp(29px, 3.2vw, 44px); line-height:1.05; letter-spacing:-.045em; }
    h2 { font-size:20px; letter-spacing:-.03em; }
    h3 { font-size:15px; }
    .page-head p { margin-top:9px; color:var(--muted); font-size:15px; }
    .head-actions { display:flex; gap:8px; flex-wrap:wrap; justify-content:flex-end; }
    .button { padding:10px 14px; color:var(--ink); background:#e8eee9; border-radius:9px; font-weight:750; transition:transform .18s ease, box-shadow .18s ease, background .18s ease; }
    .button:hover { transform:translateY(-1px); box-shadow:0 8px 18px rgba(20,39,55,.12); }
    .button.primary { color:#fff; background:var(--green); }
    .button.quiet { background:#f0eee8; }
    .toast { position:fixed; right:24px; bottom:24px; z-index:10; padding:12px 15px; color:#fff; background:var(--navy); border-radius:10px; box-shadow:var(--shadow); transform:translateY(18px); opacity:0; pointer-events:none; transition:opacity .18s ease, transform .18s ease; }
    .toast.show { opacity:1; transform:translateY(0); }
    .view { display:none; animation:fade-in .22s ease both; }
    .view.active { display:block; }
    @keyframes fade-in { from { opacity:0; transform:translateY(5px); } to { opacity:1; transform:none; } }
    .kpis { display:grid; grid-template-columns:repeat(4, minmax(0,1fr)); gap:13px; margin-bottom:20px; }
    .kpi, .panel { background:var(--surface); border:1px solid var(--line); box-shadow:var(--shadow); }
    .kpi { min-height:140px; padding:19px 20px; border-radius:13px; }
    .kpi.warning { background:#fffaf0; border-color:#efdfbb; }
    .kpi-label { display:flex; align-items:center; justify-content:space-between; color:var(--muted); font-size:12px; letter-spacing:.04em; }
    .kpi-symbol { width:29px; height:29px; display:grid; place-items:center; color:var(--green); background:#d9f4e2; border-radius:8px; font-weight:850; }
    .kpi.warning .kpi-symbol { color:var(--amber); background:var(--amber-bg); }
    .kpi-value { margin-top:12px; font-size:29px; font-weight:800; letter-spacing:-.045em; }
    .kpi-foot { margin-top:8px; color:var(--muted); font-size:12px; }
    .positive { color:var(--green); font-weight:750; }
    .negative { color:var(--red); font-weight:750; }
    .grid-2 { display:grid; grid-template-columns:1.08fr .92fr; gap:20px; margin-bottom:20px; }
    .panel { min-width:0; padding:21px; border-radius:13px; }
    .panel-head { display:flex; align-items:start; justify-content:space-between; gap:15px; margin-bottom:17px; }
    .panel-head p { margin-top:4px; color:var(--muted); font-size:12px; }
    .link-button { color:var(--green-dark); background:transparent; font-weight:750; }
    .chart-wrap { height:252px; padding-top:7px; }
    .chart-wrap svg { width:100%; height:100%; overflow:visible; }
    .chart-grid { stroke:#e6e9e2; stroke-width:1; }
    .chart-line { fill:none; stroke:var(--green); stroke-width:3; stroke-linecap:round; stroke-linejoin:round; }
    .chart-area { fill:url(#area); }
    .chart-point { fill:#fff; stroke:var(--green); stroke-width:3; }
    .axis { fill:#89959a; font-size:11px; }
    .chart-legend { display:flex; gap:18px; color:var(--muted); font-size:12px; }
    .legend-line { display:inline-block; width:21px; margin:0 6px 3px 0; border-top:2px solid var(--green); }
    .legend-dash { border-top-style:dashed; border-color:#80caa0; }
    .risk-table, .data-table { width:100%; border-collapse:collapse; }
    .risk-table th, .risk-table td, .data-table th, .data-table td { padding:11px 8px; border-bottom:1px solid #edf0ea; text-align:left; white-space:nowrap; }
    .risk-table th, .data-table th { color:var(--muted); font-size:11px; font-weight:650; }
    .risk-table td, .data-table td { font-size:12px; }
    .risk-table tr:last-child td, .data-table tr:last-child td { border-bottom:0; }
    .severity { display:inline-block; padding:3px 8px; border-radius:6px; font-size:11px; font-weight:750; }
    .severity.high { color:var(--red); background:var(--red-bg); }
    .severity.medium { color:#986c18; background:var(--amber-bg); }
    .severity.low { color:var(--green-dark); background:#dff3e5; }
    .activity { display:grid; }
    .activity-row { display:grid; grid-template-columns:124px 110px 1fr; gap:15px; align-items:center; padding:12px 0; border-bottom:1px solid #edf0ea; }
    .activity-row:last-child { border-bottom:0; }
    .activity-time { color:var(--muted); font-size:12px; }
    .activity-tag { display:inline-block; width:max-content; padding:4px 8px; color:var(--green-dark); background:#ddf1e4; border-radius:6px; font-size:11px; font-weight:750; }
    .activity-tag.warn { color:#986c18; background:var(--amber-bg); }
    .activity-text { color:#4c5a61; font-size:13px; }
    .metric-strip { display:grid; grid-template-columns:repeat(3,1fr); gap:13px; margin-bottom:20px; }
    .metric-card { padding:18px; background:var(--surface); border:1px solid var(--line); border-radius:12px; }
    .metric-card label { display:block; color:var(--muted); font-size:12px; }
    .metric-card strong { display:block; margin-top:8px; font-size:26px; letter-spacing:-.04em; }
    .table-panel { overflow:auto; }
    .table-note { margin-top:13px; color:var(--muted); font-size:12px; }
    .bar-chart { display:grid; gap:13px; }
    .bar-row { display:grid; grid-template-columns:84px 1fr 70px; gap:10px; align-items:center; font-size:12px; }
    .bar-track { height:11px; overflow:hidden; background:#edf1ec; border-radius:99px; }
    .bar-fill { height:100%; background:var(--green); border-radius:inherit; }
    .bar-fill.amber { background:#e7ae4f; }
    .bar-fill.red { background:#dc7a6e; }
    .bar-value { color:var(--muted); text-align:right; }
    .ofa-hero { display:grid; grid-template-columns:1fr 230px; gap:20px; align-items:stretch; margin-bottom:20px; }
    .ofa-status { display:flex; align-items:center; gap:10px; margin-top:12px; color:var(--muted); }
    .ofa-total { padding:20px; background:#e4f5e8; border:1px solid #c3e5cb; border-radius:12px; }
    .ofa-total label { display:block; color:var(--green-dark); font-size:12px; }
    .ofa-total strong { display:block; margin-top:7px; color:var(--green-dark); font-size:32px; letter-spacing:-.05em; }
    .ofa-total small { color:var(--green-dark); }
    .cash-grid { display:grid; grid-template-columns:1fr 1fr; gap:20px; }
    .cash-bars { height:280px; display:flex; align-items:end; gap:18px; padding:22px 10px 10px; border-bottom:1px solid var(--line); }
    .cash-bar { flex:1; display:flex; flex-direction:column; align-items:center; gap:7px; color:var(--muted); font-size:11px; }
    .cash-bar i { display:block; width:100%; max-width:42px; min-height:12px; background:var(--green); border-radius:7px 7px 2px 2px; box-shadow:0 7px 12px rgba(31,137,90,.18); }
    .cash-bar strong { color:var(--ink); font-size:12px; }
    .budget-row { display:grid; grid-template-columns:150px 1fr 70px; gap:14px; align-items:center; padding:14px 0; border-bottom:1px solid #edf0ea; }
    .budget-row:last-child { border-bottom:0; }
    .budget-row label { font-size:12px; }
    .budget-row small { display:block; color:var(--muted); }
    .progress { height:9px; overflow:hidden; background:#edf1ec; border-radius:99px; }
    .progress i { display:block; height:100%; background:var(--green); border-radius:inherit; }
    .progress i.warn { background:#e7ae4f; }
    .evidence-list { display:grid; gap:10px; }
    .evidence-item { display:grid; grid-template-columns:10px 120px 1fr; gap:12px; align-items:start; padding:11px 0; border-bottom:1px solid #edf0ea; }
    .evidence-item:last-child { border-bottom:0; }
    .evidence-dot { width:8px; height:8px; margin-top:6px; background:var(--green); border-radius:50%; box-shadow:0 0 0 4px #e0f3e6; }
    .evidence-time { color:var(--muted); font-size:12px; }
    .evidence-text { color:#4c5a61; font-size:13px; }
    @media (max-width:1050px) { .app { grid-template-columns:82px minmax(0,1fr); } .sidebar { padding:20px 10px; } .brand { justify-content:center; padding-left:0; padding-right:0; } .brand > div:not(.brand-mark), .workspace, .nav button span:not(.nav-icon), .sidebar-footer { display:none; } .nav button { justify-content:center; padding:13px 8px; } .kpis { grid-template-columns:repeat(2,1fr); } .page { width:min(94%, 1450px); } }
    @media (max-width:760px) { .topbar { height:auto; min-height:65px; padding:14px 18px; gap:10px; } .topbar-left strong { font-size:14px; } .topbar-right { gap:9px; font-size:11px; } .period { display:none; } .page { width:calc(100% - 32px); padding-top:25px; } .page-head { display:block; } .head-actions { justify-content:flex-start; margin-top:15px; } .grid-2, .cash-grid, .ofa-hero { grid-template-columns:1fr; } .metric-strip { grid-template-columns:1fr 1fr; } .activity-row { grid-template-columns:1fr; gap:4px; } .budget-row { grid-template-columns:110px 1fr 58px; gap:9px; } }
    @media (max-width:480px) { .app { grid-template-columns:1fr; } .sidebar { position:sticky; top:0; z-index:8; height:64px; padding:10px 12px; flex-direction:row; align-items:center; gap:10px; overflow:auto; } .brand { border:0; padding:0; } .brand-mark { width:35px; height:35px; } .nav { display:flex; gap:5px; } .nav button { width:44px; height:40px; flex:0 0 auto; } .main { min-width:0; } .topbar { padding-left:16px; } .topbar-left { min-width:0; } .topbar-left strong { white-space:nowrap; overflow:hidden; text-overflow:ellipsis; } .data-status { display:none; } .kpis, .metric-strip { grid-template-columns:1fr 1fr; gap:9px; } .kpi { min-height:115px; padding:14px; } .kpi-value { font-size:21px; } .kpi-symbol { display:none; } .panel { padding:16px; } .risk-table th, .risk-table td, .data-table th, .data-table td { padding-left:5px; padding-right:5px; } }
    @media (prefers-reduced-motion: reduce) { *, *::before, *::after { scroll-behavior:auto !important; transition-duration:.01ms !important; animation-duration:.01ms !important; } }
  </style>
</head>
<body>
  <div class="app">
    <aside class="sidebar" aria-label="FAC modules">
      <div class="brand"><div class="brand-mark">F</div><div><strong>FAC</strong><small>Finance Autonomous Center</small></div></div>
      <div class="workspace">制造企业 · 财经运营中枢</div>
      <nav class="nav">
        <button class="active" data-view="overview" aria-current="page"><span class="nav-icon">⌂</span><span>总览</span></button>
        <button data-view="revenue"><span class="nav-icon">▥</span><span>收入与毛利</span></button>
        <button data-view="ofa"><span class="nav-icon">◇</span><span>订单财经</span></button>
        <button data-view="ar"><span class="nav-icon">▤</span><span>应收 AR</span></button>
        <button data-view="cash"><span class="nav-icon">◎</span><span>资金 Cash</span></button>
        <button data-view="budget"><span class="nav-icon">▣</span><span>预算 Budget</span></button>
        <button data-view="risk"><span class="nav-icon">♢</span><span>风险与证据</span></button>
      </nav>
      <div class="sidebar-footer"><strong>本地演示环境</strong><span>EDP Mock · Management Finance</span></div>
    </aside>
    <section class="main">
      <header class="topbar">
        <div class="topbar-left"><div class="factory-icon">⌂</div><strong>制造企业 FAC 财经工作台</strong></div>
        <div class="topbar-right"><select class="period" id="period"><option>2025 年 01 月</option><option>2024 年 12 月</option><option>2024 年 11 月</option></select><div class="data-status"><span class="dot"></span><span id="sync-status">数据状态：已更新 · 10:05</span></div><div class="user">林</div></div>
      </header>
      <main class="page">
        <div class="toast" id="toast" role="status"></div>
        <section class="view active" data-view-panel="overview">
          <div class="page-head"><div><h1>财经健康总览</h1><p>面向制造业务的收入、毛利、回款与资金经营总览。</p></div><div class="head-actions"><button class="button quiet" data-period-action="month">月度口径</button><button class="button primary" id="run-ofa">运行订单财经演示</button></div></div>
          <div class="kpis">
            <article class="kpi"><div class="kpi-label"><span>Revenue</span><span class="kpi-symbol">▥</span></div><div class="kpi-value">¥ 28.46 亿</div><div class="kpi-foot">较上月 <span class="positive">+6.8% ▲</span></div></article>
            <article class="kpi"><div class="kpi-label"><span>Gross Margin</span><span class="kpi-symbol">%</span></div><div class="kpi-value">22.9%</div><div class="kpi-foot">较上月 <span class="positive">+1.6 pct ▲</span></div></article>
            <article class="kpi warning"><div class="kpi-label"><span>AR Overdue</span><span class="kpi-symbol">!</span></div><div class="kpi-value">¥ 3.72 亿</div><div class="kpi-foot">占应收 13.1% · 较上月 <span class="positive">-1.9 pct ▼</span></div></article>
            <article class="kpi"><div class="kpi-label"><span>Cash 30D</span><span class="kpi-symbol">◎</span></div><div class="kpi-value">¥ 9.68 亿</div><div class="kpi-foot">较上月 <span class="positive">+12.4% ▲</span></div></article>
          </div>
          <div class="grid-2">
            <article class="panel"><div class="panel-head"><div><h2>毛利率趋势</h2><p>Revenue 与 Cost Fact 聚合结果</p></div><div class="chart-legend"><span><i class="legend-line"></i>毛利率</span><span><i class="legend-line legend-dash"></i>目标 22.0%</span></div></div><div class="chart-wrap"><svg viewBox="0 0 650 245" role="img" aria-label="毛利率趋势图"><defs><linearGradient id="area" x1="0" x2="0" y1="0" y2="1"><stop offset="0" stop-color="#bdebd0" stop-opacity=".8"/><stop offset="1" stop-color="#bdebd0" stop-opacity=".08"/></linearGradient></defs><line x1="45" y1="35" x2="630" y2="35" class="chart-grid"/><line x1="45" y1="90" x2="630" y2="90" class="chart-grid"/><line x1="45" y1="145" x2="630" y2="145" class="chart-grid"/><line x1="45" y1="200" x2="630" y2="200" class="chart-grid"/><line x1="45" y1="99" x2="630" y2="99" stroke="#84cba1" stroke-dasharray="6 7"/><path class="chart-area" d="M45 151 L140 139 L235 127 L330 119 L425 101 L520 82 L630 75 L630 200 L45 200 Z"/><path class="chart-line" d="M45 151 L140 139 L235 127 L330 119 L425 101 L520 82 L630 75"/><g class="chart-point"><circle cx="45" cy="151" r="5"/><circle cx="140" cy="139" r="5"/><circle cx="235" cy="127" r="5"/><circle cx="330" cy="119" r="5"/><circle cx="425" cy="101" r="5"/><circle cx="520" cy="82" r="5"/><circle cx="630" cy="75" r="5"/></g><g class="axis"><text x="4" y="39">26.0%</text><text x="4" y="94">24.0%</text><text x="4" y="149">22.0%</text><text x="4" y="204">20.0%</text><text x="28" y="230">2024-07</text><text x="123" y="230">2024-08</text><text x="218" y="230">2024-09</text><text x="313" y="230">2024-10</text><text x="408" y="230">2024-11</text><text x="503" y="230">2024-12</text><text x="600" y="230">2025-01</text></g><g fill="#1f895a" font-weight="750" font-size="12"><text x="609" y="63">22.9%</text></g></svg></div></article>
            <article class="panel"><div class="panel-head"><div><h2>风险待办队列</h2><p>Finance Risk · DecisionCase</p></div><button class="link-button" data-view-link="risk">查看全部 ›</button></div><table class="risk-table"><thead><tr><th>风险事项</th><th>级别</th><th>影响</th><th>责任人</th></tr></thead><tbody><tr><td>客户 A 应收逾期扩大</td><td><span class="severity high">高</span></td><td>¥ 1.18 亿</td><td>应收管理组</td></tr><tr><td>订单 B 毛利率低于底线</td><td><span class="severity high">高</span></td><td>-3.2 pct</td><td>订单财经组</td></tr><tr><td>原材料（铜）成本上涨</td><td><span class="severity medium">中</span></td><td>毛利 -1.1 pct</td><td>成本管理组</td></tr><tr><td>制造费用预算执行偏差</td><td><span class="severity medium">中</span></td><td>+8.4%</td><td>预算管理组</td></tr></tbody></table></article>
          </div>
          <article class="panel"><div class="panel-head"><div><h2>证据与活动动态</h2><p>Result → Evidence → Verify 的最近动作</p></div><button class="link-button" data-view-link="risk">查看全部活动 ›</button></div><div class="activity"><div class="activity-row"><span class="activity-time">2025-01-24 10:05</span><span class="activity-tag">数据更新</span><span class="activity-text">完成日常数据处理：收入、订单、应收、资金等数据已更新至 2025-01-24。</span></div><div class="activity-row"><span class="activity-time">2025-01-24 09:32</span><span class="activity-tag">证据归档</span><span class="activity-text">订单 B 毛利率评估证据已归档，已关联风险 #R-250124-02。</span></div><div class="activity-row"><span class="activity-time">2025-01-23 17:48</span><span class="activity-tag warn">风险处置</span><span class="activity-text">客户 A 逾期风险推进：已完成对账，并发出回款计划确认函。</span></div><div class="activity-row"><span class="activity-time">2025-01-23 15:20</span><span class="activity-tag">预算跟踪</span><span class="activity-text">制造费用预算执行率 108.4%，已发起费用复核与控制建议。</span></div></div></article>
        </section>
        <section class="view" data-view-panel="revenue"><div class="page-head"><div><h1>收入与毛利</h1><p>从 Revenue Fact 到 Margin Result，按客户、产品与订单穿透经营结果。</p></div><div class="head-actions"><button class="button quiet" data-period-action="quarter">季度口径</button><button class="button primary" data-action="export">导出管理结果</button></div></div><div class="metric-strip"><div class="metric-card"><label>本期收入</label><strong>¥ 28.46 亿</strong><span class="positive">+6.8% MoM</span></div><div class="metric-card"><label>订单毛利</label><strong>22.9%</strong><span class="positive">+1.6 pct MoM</span></div><div class="metric-card"><label>低毛利订单</label><strong>18 个</strong><span class="negative">4 个需复核</span></div></div><div class="grid-2"><article class="panel"><div class="panel-head"><div><h2>产品线收入贡献</h2><p>RevenueFact / product_id</p></div></div><div class="bar-chart"><div class="bar-row"><span>工业控制</span><div class="bar-track"><i class="bar-fill" style="width:86%"></i></div><span class="bar-value">¥ 12.4 亿</span></div><div class="bar-row"><span>能源设备</span><div class="bar-track"><i class="bar-fill" style="width:68%"></i></div><span class="bar-value">¥ 8.7 亿</span></div><div class="bar-row"><span>汽车零部件</span><div class="bar-track"><i class="bar-fill" style="width:49%"></i></div><span class="bar-value">¥ 4.2 亿</span></div><div class="bar-row"><span>其他业务</span><div class="bar-track"><i class="bar-fill" style="width:31%"></i></div><span class="bar-value">¥ 3.1 亿</span></div></div></article><article class="panel table-panel"><div class="panel-head"><div><h2>重点客户毛利</h2><p>MarginResult / customer_id</p></div></div><table class="data-table"><thead><tr><th>客户</th><th>收入</th><th>毛利率</th><th>状态</th></tr></thead><tbody><tr><td>客户 A</td><td>¥ 6.21 亿</td><td>25.6%</td><td><span class="severity low">健康</span></td></tr><tr><td>客户 B</td><td>¥ 4.88 亿</td><td class="negative">18.8%</td><td><span class="severity high">复核</span></td></tr><tr><td>客户 C</td><td>¥ 3.65 亿</td><td>23.4%</td><td><span class="severity low">健康</span></td></tr><tr><td>客户 D</td><td>¥ 2.94 亿</td><td>21.7%</td><td><span class="severity medium">关注</span></td></tr></tbody></table></article></div></section>
        <section class="view" data-view-panel="ofa"><div class="page-head"><div><h1>订单财经分析库</h1><p>真实 OFA 计算、版本冻结、重放幂等与证据链路。</p></div><div class="head-actions"><a class="button quiet" href="/demo/fac">打开 OFA 明细页</a><button class="button primary" id="run-ofa-inline">运行 OFA 演示</button></div></div><div class="ofa-hero"><article class="panel"><div class="panel-head"><div><h2>ORD-1001 · PROD-1001</h2><p>Demo Order · EDP projection · Price revision V1 / V2</p></div><span class="severity low">EDP READY</span></div><div class="ofa-status"><span class="dot"></span><span id="ofa-status">等待运行 OFA 计算</span></div><p class="table-note">OFA 通过 OrderDataPort、BOMDataPort、MaterialPricePort、LaborCostPort 与 ExpensePort 消费输入；缺失关键价格不会默认为 0。</p></article><div class="ofa-total"><label>当前计划成本</label><strong id="ofa-total">—</strong><small id="ofa-version">尚未生成版本</small></div></div><article class="panel table-panel"><div class="panel-head"><div><h2>OFA Result / Evidence</h2><p>Result → Calculation Snapshot → Frozen Input Refs</p></div></div><table class="data-table"><thead><tr><th>版本</th><th>物料</th><th>人工</th><th>费用</th><th>总成本</th><th>Evidence</th></tr></thead><tbody><tr><td>V1 · Initial quote</td><td>24.00 CNY</td><td>20.00 CNY</td><td>2.00 CNY</td><td>46.00 CNY</td><td><span class="severity low">已冻结</span></td></tr><tr><td>V2 · Material revision</td><td>30.00 CNY</td><td>20.00 CNY</td><td>2.00 CNY</td><td>52.00 CNY</td><td><span class="severity low">已冻结</span></td></tr></tbody></table></article></section>
        <section class="view" data-view-panel="ar"><div class="page-head"><div><h1>应收 AR 工作台</h1><p>从发票、到期、逾期到催收 DecisionCase 的可追踪闭环。</p></div><div class="head-actions"><button class="button quiet" data-action="refresh">刷新数据</button><button class="button primary" data-action="collect">生成催收建议</button></div></div><div class="metric-strip"><div class="metric-card"><label>应收余额</label><strong>¥ 28.40 亿</strong><span>较上月 +2.4%</span></div><div class="metric-card"><label>逾期余额</label><strong>¥ 3.72 亿</strong><span class="negative">占比 13.1%</span></div><div class="metric-card"><label>本月预计回款</label><strong>¥ 8.26 亿</strong><span class="positive">覆盖率 91.2%</span></div></div><div class="grid-2"><article class="panel"><div class="panel-head"><div><h2>应收账龄</h2><p>Receivable → Due → Overdue</p></div></div><div class="bar-chart"><div class="bar-row"><span>未到期</span><div class="bar-track"><i class="bar-fill" style="width:74%"></i></div><span class="bar-value">¥ 21.02 亿</span></div><div class="bar-row"><span>1–30 天</span><div class="bar-track"><i class="bar-fill amber" style="width:45%"></i></div><span class="bar-value">¥ 3.18 亿</span></div><div class="bar-row"><span>31–90 天</span><div class="bar-track"><i class="bar-fill amber" style="width:31%"></i></div><span class="bar-value">¥ 2.21 亿</span></div><div class="bar-row"><span>90 天以上</span><div class="bar-track"><i class="bar-fill red" style="width:21%"></i></div><span class="bar-value">¥ 1.51 亿</span></div></div></article><article class="panel table-panel"><div class="panel-head"><div><h2>重点催收对象</h2><p>AR Risk · Accountable Owner</p></div></div><table class="data-table"><thead><tr><th>客户</th><th>逾期金额</th><th>账龄</th><th>风险</th><th>动作</th></tr></thead><tbody><tr><td>客户 A</td><td>¥ 1.18 亿</td><td>61 天</td><td><span class="severity high">高</span></td><td><button class="link-button" data-action="collect">生成建议</button></td></tr><tr><td>客户 E</td><td>¥ 0.72 亿</td><td>35 天</td><td><span class="severity medium">中</span></td><td><button class="link-button" data-action="collect">生成建议</button></td></tr><tr><td>客户 H</td><td>¥ 0.46 亿</td><td>18 天</td><td><span class="severity medium">中</span></td><td><button class="link-button" data-action="collect">生成建议</button></td></tr></tbody></table></article></div></section>
        <section class="view" data-view-panel="cash"><div class="page-head"><div><h1>资金 Cash</h1><p>当前现金位置与 7D / 30D / 90D 现金预测。</p></div><div class="head-actions"><button class="button quiet" data-action="refresh">刷新预测</button><button class="button primary" data-action="export">生成资金简报</button></div></div><div class="metric-strip"><div class="metric-card"><label>当前现金</label><strong>¥ 12.84 亿</strong><span class="positive">安全边际 +18.2%</span></div><div class="metric-card"><label>Cash 30D</label><strong>¥ 9.68 亿</strong><span class="positive">净增加 ¥ 1.06 亿</span></div><div class="metric-card"><label>最低现金点</label><strong>¥ 8.92 亿</strong><span>2025-02-07</span></div></div><div class="cash-grid"><article class="panel"><div class="panel-head"><div><h2>现金预测</h2><p>Opening Cash + Collection − AP − Commitments</p></div></div><div class="cash-bars"><div class="cash-bar"><strong>12.84</strong><i style="height:215px"></i><span>当前</span></div><div class="cash-bar"><strong>11.32</strong><i style="height:190px"></i><span>7D</span></div><div class="cash-bar"><strong>9.68</strong><i style="height:160px"></i><span>30D</span></div><div class="cash-bar"><strong>10.24</strong><i style="height:171px"></i><span>60D</span></div><div class="cash-bar"><strong>11.06</strong><i style="height:184px"></i><span>90D</span></div></div></article><article class="panel"><div class="panel-head"><div><h2>未来 30 天现金承诺</h2><p>已确认支出与风险缓冲</p></div></div><table class="data-table"><tbody><tr><td>供应商付款</td><td>¥ 4.72 亿</td><td><span class="severity low">已计划</span></td></tr><tr><td>工资与社保</td><td>¥ 1.28 亿</td><td><span class="severity low">已计划</span></td></tr><tr><td>税费</td><td>¥ 0.96 亿</td><td><span class="severity medium">待核对</span></td></tr><tr><td>资本性支出</td><td>¥ 0.44 亿</td><td><span class="severity medium">审批中</span></td></tr></tbody></table></article></div></section>
        <section class="view" data-view-panel="budget"><div class="page-head"><div><h1>预算 Budget</h1><p>目标 → 预算 → 实际 → 偏差 → 决策，保持责任与证据关联。</p></div><div class="head-actions"><button class="button quiet" data-action="refresh">刷新执行率</button><button class="button primary" data-action="export">导出预算简报</button></div></div><div class="metric-strip"><div class="metric-card"><label>年度预算</label><strong>¥ 31.20 亿</strong><span>已执行 7.48%</span></div><div class="metric-card"><label>本月执行率</label><strong>108.4%</strong><span class="negative">超预算 +8.4%</span></div><div class="metric-card"><label>待处理偏差</label><strong>6 项</strong><span class="negative">2 项高优先级</span></div></div><article class="panel"><div class="panel-head"><div><h2>费用预算执行</h2><p>BudgetExecution / cost_center / evidence_ref</p></div></div><div class="budget-row"><label>制造费用<small>预算 ¥ 1.20 亿</small></label><div class="progress"><i class="warn" style="width:86%"></i></div><strong class="negative">108.4%</strong></div><div class="budget-row"><label>研发费用<small>预算 ¥ 0.68 亿</small></label><div class="progress"><i style="width:71%"></i></div><strong>94.2%</strong></div><div class="budget-row"><label>销售费用<small>预算 ¥ 0.52 亿</small></label><div class="progress"><i style="width:62%"></i></div><strong>88.7%</strong></div><div class="budget-row"><label>管理费用<small>预算 ¥ 0.34 亿</small></label><div class="progress"><i class="warn" style="width:77%"></i></div><strong class="negative">102.1%</strong></div></article></section>
        <section class="view" data-view-panel="risk"><div class="page-head"><div><h1>风险与证据</h1><p>Finance Risk、DecisionCase 与 Evidence 的统一追踪入口。</p></div><div class="head-actions"><button class="button quiet" data-action="refresh">刷新队列</button><button class="button primary" data-action="export">生成风险简报</button></div></div><article class="panel table-panel" style="margin-bottom:20px"><div class="panel-head"><div><h2>风险待办队列</h2><p>所有高风险事项保留 Accountable Owner，不允许 Agent 自行 Verify。</p></div></div><table class="risk-table"><thead><tr><th>风险事项</th><th>级别</th><th>影响</th><th>责任人</th><th>到期日</th><th>状态</th></tr></thead><tbody><tr><td>客户 A 应收逾期扩大</td><td><span class="severity high">高</span></td><td>¥ 1.18 亿</td><td>应收管理组</td><td>2025-01-27</td><td><span class="severity medium">处理中</span></td></tr><tr><td>订单 B 毛利率低于底线</td><td><span class="severity high">高</span></td><td>-3.2 pct</td><td>订单财经组</td><td>2025-01-26</td><td><span class="severity high">待复核</span></td></tr><tr><td>原材料（铜）成本上涨</td><td><span class="severity medium">中</span></td><td>毛利 -1.1 pct</td><td>成本管理组</td><td>2025-01-31</td><td><span class="severity low">已确认</span></td></tr><tr><td>制造费用预算执行偏差</td><td><span class="severity medium">中</span></td><td>+8.4%</td><td>预算管理组</td><td>2025-02-05</td><td><span class="severity medium">待解释</span></td></tr></tbody></table></article><article class="panel"><div class="panel-head"><div><h2>Evidence 活动链</h2><p>Result → Calculation Snapshot → Source Object → Evidence</p></div></div><div class="evidence-list"><div class="evidence-item"><span class="evidence-dot"></span><span class="evidence-time">10:05 · Data update</span><span class="evidence-text">收入、订单、应收与资金数据已更新；批次 EDP-20250124-1005 校验通过。</span></div><div class="evidence-item"><span class="evidence-dot"></span><span class="evidence-time">09:32 · Evidence</span><span class="evidence-text">ORD-1001 V2 计划成本结果已绑定 BOM、MaterialPrice rev 2 与 rule v1。</span></div><div class="evidence-item"><span class="evidence-dot"></span><span class="evidence-time">昨日 17:48 · DecisionCase</span><span class="evidence-text">客户 A 催收建议已生成，等待 Accountable Owner 确认。</span></div><div class="evidence-item"><span class="evidence-dot"></span><span class="evidence-time">昨日 15:20 · Budget</span><span class="evidence-text">制造费用偏差已关联责任人、预算版本与费用明细 Evidence。</span></div></div></article></section>
      </main>
    </section>
  </div>
  <script>
    const qs = (selector, root = document) => root.querySelector(selector);
    const qsa = (selector, root = document) => [...root.querySelectorAll(selector)];
    const toast = (message) => { const element = qs("#toast"); element.textContent = message; element.classList.add("show"); window.clearTimeout(window.facToastTimer); window.facToastTimer = window.setTimeout(() => element.classList.remove("show"), 2600); };
    const api = async (path, options = {}) => { const response = await fetch(path, { headers:{"Content-Type":"application/json"}, ...options }); const payload = await response.json(); if (!response.ok) throw new Error(payload.detail || `HTTP ${response.status}`); return payload; };
    const setView = (name) => { qsa(".nav button").forEach((button) => { const active = button.dataset.view === name; button.classList.toggle("active", active); if (active) button.setAttribute("aria-current", "page"); else button.removeAttribute("aria-current"); }); qsa(".view").forEach((panel) => panel.classList.toggle("active", panel.dataset.viewPanel === name)); window.scrollTo({top:0, behavior:"smooth"}); };
    qsa(".nav button").forEach((button) => button.addEventListener("click", () => setView(button.dataset.view)));
    qsa("[data-view-link]").forEach((button) => button.addEventListener("click", () => setView(button.dataset.viewLink)));
    qsa("[data-period-action]").forEach((button) => button.addEventListener("click", () => toast(`已切换为${button.textContent.trim()}，演示数据已刷新`)));
    qsa("[data-action='export']").forEach((button) => button.addEventListener("click", () => toast("管理简报已生成，可进入 Evidence 查看来源")));
    qsa("[data-action='refresh']").forEach((button) => button.addEventListener("click", () => toast("数据队列已刷新，所有结果保留 Evidence 引用")));
    qsa("[data-action='collect']").forEach((button) => button.addEventListener("click", () => { button.textContent = "已生成"; button.style.color = "var(--green-dark)"; toast("催收 DecisionCase 已生成，等待责任人确认"); }));
    const runOFA = async () => { const button = qs("#run-ofa"); const inline = qs("#run-ofa-inline"); [button, inline].filter(Boolean).forEach((item) => { item.disabled = true; item.textContent = "计算中…"; }); try { await api("/api/v1/demo/reset", {method:"POST"}); const first = {order_id:"ORD-1001", price_revision:1, event_id:"demo-event-v1", idempotency_key:"demo-key-v1", trigger_type:"QuoteRecalculationRequired", reason:"Initial quote", actor:"demo-user"}; await api("/api/v1/demo/events/quote-recalculation", {method:"POST", body:JSON.stringify(first)}); const second = {...first, price_revision:2, event_id:"demo-event-v2", idempotency_key:"demo-key-v2", reason:"MaterialPriceRevision"}; const result = await api("/api/v1/demo/events/quote-recalculation", {method:"POST", body:JSON.stringify(second)}); const total = result.result.total_cost.functional_amount; qs("#ofa-total").textContent = `${total} CNY`; qs("#ofa-version").textContent = `Calculation V${result.result.version} · Evidence 已冻结`; qs("#ofa-status").textContent = "OFA V2 计算完成 · replay-safe"; qs("#sync-status").textContent = "数据状态：刚刚更新 · OFA V2"; toast("订单财经演示完成：V1 46.00 → V2 52.00 CNY"); } catch (error) { qs("#ofa-status").textContent = error.message; toast(`OFA 演示失败：${error.message}`); } finally { [button, inline].filter(Boolean).forEach((item) => { item.disabled = false; item.textContent = item.id === "run-ofa" ? "运行订单财经演示" : "运行 OFA 演示"; }); } };
    qs("#run-ofa").addEventListener("click", runOFA); qs("#run-ofa-inline").addEventListener("click", runOFA);
  </script>
</body>
</html>'''
