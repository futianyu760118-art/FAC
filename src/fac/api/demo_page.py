"""Self-contained browser page for the local FAC finance demo."""


def render_demo_page() -> str:
    return r'''<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>FAC Demo · Finance Autonomous Center</title>
  <style>
    :root { --ink:#14202b; --muted:#687582; --paper:#f4f1ea; --panel:#fffdf8;
      --line:#ddd8ce; --navy:#162733; --mint:#d7f1dc; --green:#23734a;
      --amber:#b46b21; --red:#a4403a; --shadow:0 18px 48px rgba(20,32,43,.08); }
    * { box-sizing:border-box; }
    body { margin:0; color:var(--ink); background:var(--paper); font:15px/1.55 Inter,
      ui-sans-serif, system-ui, -apple-system, "Segoe UI", sans-serif; }
    button { border:0; cursor:pointer; font:inherit; }
    .topbar { min-height:72px; padding:0 5vw; display:flex; align-items:center;
      justify-content:space-between; color:#fff; background:var(--navy); }
    .brand { display:flex; align-items:center; gap:12px; letter-spacing:.03em; }
    .brand-mark { width:34px; height:34px; display:grid; place-items:center; color:var(--navy);
      background:#b9e6c0; border-radius:9px; font-weight:800; }
    .brand small { display:block; color:#a9bcc5; font-size:11px; letter-spacing:.14em; }
    .demo-tag { padding:7px 11px; color:#d7f1dc; border:1px solid #55756b; border-radius:999px;
      font-size:11px; letter-spacing:.13em; text-transform:uppercase; }
    .shell { width:min(1360px, 90vw); margin:38px auto 70px; }
    .intro { display:flex; align-items:end; justify-content:space-between; gap:30px; margin-bottom:24px; }
    h1,h2,h3,p { margin:0; }
    h1 { font-size:clamp(28px, 4vw, 48px); letter-spacing:-.045em; line-height:1.02; }
    .intro-copy { max-width:640px; }
    .intro-copy p { margin-top:12px; color:var(--muted); }
    .order-pill { padding:15px 18px; background:var(--panel); border:1px solid var(--line);
      border-radius:14px; box-shadow:var(--shadow); white-space:nowrap; }
    .order-pill span { display:block; color:var(--muted); font-size:11px; letter-spacing:.12em;
      text-transform:uppercase; }
    .layout { display:grid; grid-template-columns:220px minmax(0,1fr); gap:22px; }
    .rail, .panel { background:var(--panel); border:1px solid var(--line); box-shadow:var(--shadow); }
    .rail { align-self:start; padding:18px; border-radius:18px; }
    .rail h2 { margin-bottom:18px; font-size:12px; color:var(--muted); letter-spacing:.12em;
      text-transform:uppercase; }
    .step { display:flex; gap:11px; padding:13px 0; border-top:1px solid #ece8df; }
    .step:first-of-type { border-top:0; }
    .step-no { width:24px; height:24px; display:grid; place-items:center; flex:0 0 auto;
      background:#e8e5dd; border-radius:50%; color:var(--muted); font-size:11px; font-weight:700; }
    .step strong { display:block; font-size:13px; }
    .step small { color:var(--muted); font-size:11px; }
    .content { display:grid; gap:22px; min-width:0; }
    .panel { padding:24px; border-radius:18px; }
    .panel-heading { display:flex; align-items:start; justify-content:space-between; gap:18px; margin-bottom:20px; }
    .eyebrow { color:var(--green); font-size:11px; font-weight:750; letter-spacing:.14em; text-transform:uppercase; }
    h2 { margin-top:4px; font-size:22px; letter-spacing:-.03em; }
    .muted { color:var(--muted); }
    .actions { display:flex; flex-wrap:wrap; gap:9px; }
    .button { padding:11px 14px; border-radius:10px; font-weight:700; transition:transform .16s ease, box-shadow .16s ease; }
    .button:hover { transform:translateY(-1px); box-shadow:0 7px 18px rgba(20,32,43,.12); }
    .primary { color:#fff; background:var(--green); }
    .secondary { color:var(--ink); background:#e9eee8; }
    .quiet { color:var(--ink); background:#efede6; }
    .status { min-height:25px; color:var(--muted); font-size:13px; }
    .status.success { color:var(--green); }
    .status.error { color:var(--red); }
    .metrics { display:grid; grid-template-columns:repeat(4,1fr); gap:11px; }
    .metric { padding:16px; background:#faf8f2; border:1px solid #ebe7dc; border-radius:13px; }
    .metric-label { color:var(--muted); font-size:11px; letter-spacing:.08em; text-transform:uppercase; }
    .metric-value { margin-top:6px; font-size:25px; font-weight:760; letter-spacing:-.04em; }
    .metric.total { color:var(--green); background:var(--mint); border-color:#b9dfc1; }
    .lower { display:grid; grid-template-columns:1.05fr .95fr; gap:22px; }
    .timeline { display:grid; gap:10px; }
    .version { display:grid; grid-template-columns:52px 1fr auto; gap:13px; align-items:center;
      padding:12px; background:#faf8f2; border:1px solid #ebe7dc; border-radius:12px; }
    .version-no { color:var(--green); font-size:18px; font-weight:800; }
    .version strong { display:block; }
    .version small { color:var(--muted); }
    .version-amount { font-weight:750; }
    .audit-grid { display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:10px 16px; }
    .audit-item { min-width:0; padding-bottom:9px; border-bottom:1px solid #ebe7dc; }
    .audit-item label { display:block; color:var(--muted); font-size:11px; letter-spacing:.08em; text-transform:uppercase; }
    .audit-item code { display:block; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; margin-top:3px;
      font:12px ui-monospace, SFMono-Regular, Consolas, monospace; }
    .refs, .events { display:grid; gap:8px; margin-top:13px; }
    .ref, .event { padding:10px 12px; color:var(--muted); background:#faf8f2; border-radius:9px; font-size:12px; }
    .event strong { color:var(--ink); }
    .empty { padding:24px 8px; color:var(--muted); text-align:center; }
    @media (max-width:850px) {
      .intro { display:block; }
      .order-pill { display:inline-block; margin-top:18px; }
      .layout, .lower { grid-template-columns:1fr; }
      .metrics { grid-template-columns:repeat(2,1fr); }
      .rail { display:grid; grid-template-columns:repeat(4,1fr); gap:8px; }
      .rail h2 { grid-column:1/-1; margin-bottom:0; }
      .step { display:block; padding:8px; border:0; }
      .step small { display:block; margin-top:3px; }
    }
    @media (max-width:540px) {
      .shell { width:min(94vw, 1360px); margin-top:24px; }
      .topbar { padding:0 3vw; }
      .panel { padding:18px; }
      .panel-heading { display:block; }
      .actions { margin-top:16px; }
      .button { width:100%; }
      .metrics { grid-template-columns:1fr 1fr; }
      .metric-value { font-size:20px; }
      .audit-grid { grid-template-columns:1fr; }
    }
  </style>
</head>
<body>
  <header class="topbar">
    <div class="brand"><div class="brand-mark">F</div><div><strong>FAC</strong><small>Finance Autonomous Center</small></div></div>
    <div class="demo-tag">Local Demo · V3</div>
  </header>
  <main class="shell">
    <section class="intro">
      <div class="intro-copy"><h1>订单财经计算工作台</h1><p>用一个真实可重放的订单场景，观察报价重算、版本冻结与财经审计链路。</p></div>
      <div class="order-pill"><span>Demo Order</span><strong>ORD-1001 · PROD-1001</strong></div>
    </section>
    <div class="layout">
      <aside class="rail" aria-label="Demo workflow">
        <h2>Workflow</h2>
        <div class="step"><div class="step-no">01</div><div><strong>数据准备</strong><small>EDP projections</small></div></div>
        <div class="step"><div class="step-no">02</div><div><strong>初次计算</strong><small>Calculation V1</small></div></div>
        <div class="step"><div class="step-no">03</div><div><strong>价格重算</strong><small>Calculation V2</small></div></div>
        <div class="step"><div class="step-no">04</div><div><strong>重放验证</strong><small>Idempotency</small></div></div>
      </aside>
      <section class="content">
        <article class="panel">
          <div class="panel-heading"><div><div class="eyebrow">Finance calculation</div><h2>计划成本结果</h2><p class="muted">所有金额来自 Demo API 的真实 OFA 计算结果。</p></div><div class="actions"><button class="button quiet" id="reset">初始化 Demo 数据</button><button class="button primary" id="calculate">运行初次计算</button><button class="button secondary" id="recalculate">价格修正并重算</button><button class="button quiet" id="replay">重放最近事件</button></div></div>
          <div class="status" id="status" role="status">等待初始化。建议按 01 → 02 → 03 → 04 操作。</div>
          <div class="metrics"><div class="metric"><div class="metric-label">Material</div><div class="metric-value" id="material">—</div></div><div class="metric"><div class="metric-label">Labor</div><div class="metric-value" id="labor">—</div></div><div class="metric"><div class="metric-label">Expense</div><div class="metric-value" id="expense">—</div></div><div class="metric total"><div class="metric-label">Plan total</div><div class="metric-value" id="total">—</div></div></div>
        </article>
        <div class="lower">
          <article class="panel"><div class="eyebrow">Version history</div><h2>计算版本时间线</h2><div class="timeline" id="timeline"><div class="empty">尚未生成 V1 / V2 结果。</div></div></article>
          <article class="panel"><div class="eyebrow">Audit trail</div><h2>审计与冻结输入</h2><div class="audit-grid" id="audit"><div class="empty">执行计算后显示 CalculationRun / CalculationSnapshot。</div></div><div class="refs" id="refs"></div></article>
        </div>
        <article class="panel"><div class="eyebrow">Event replay</div><h2>事件记录</h2><div class="events" id="events"><div class="empty">尚未记录 QuoteRecalculationRequired。</div></div></article>
      </section>
    </div>
  </main>
  <script>
    const $ = (id) => document.getElementById(id);
    let latestRequest = null;
    const requestFor = (revision) => ({ order_id:"ORD-1001", price_revision:revision,
      event_id:`demo-event-v${revision}`, idempotency_key:`demo-key-v${revision}`,
      trigger_type:"QuoteRecalculationRequired", reason:revision === 1 ? "Initial quote" : "MaterialPriceRevision", actor:"demo-user" });
    const api = async (path, options = {}) => { const response = await fetch(path, { headers:{"Content-Type":"application/json"}, ...options });
      const payload = await response.json(); if (!response.ok) throw new Error(payload.detail || `HTTP ${response.status}`); return payload; };
    const money = (value) => value ? `${value.functional_amount} ${value.functional_currency}` : "—";
    const setStatus = (message, kind = "") => { $("status").textContent = message; $("status").className = `status ${kind}`; };
    const renderResult = (result) => { if (!result) return; $("material").textContent = money(result.material_cost); $("labor").textContent = money(result.labor_cost); $("expense").textContent = money(result.expense_cost); $("total").textContent = money(result.total_cost); };
    const renderState = (state) => { const results = state.results || []; const calculations = state.calculations || [];
      if (results.length) renderResult(results[results.length - 1]);
      $("timeline").innerHTML = results.length ? results.map((result, index) => { const calc = calculations[index] || {}; return `<div class="version"><div class="version-no">V${result.version}</div><div><strong>${result.status}</strong><small>${calc.trigger_type || "Calculation"} · ${calc.reason || "—"}</small></div><div class="version-amount">${money(result.total_cost)}</div></div>`; }).join("") : `<div class="empty">尚未生成 V1 / V2 结果。</div>`;
      const latest = calculations[calculations.length - 1];
      $("audit").innerHTML = latest ? `<div class="audit-item"><label>Calculation ID</label><code>${latest.calculation_id}</code></div><div class="audit-item"><label>Snapshot ID</label><code>${latest.snapshot_id}</code></div><div class="audit-item"><label>Rule set</label><code>${latest.rule_set_version}</code></div><div class="audit-item"><label>Checksum</label><code>${latest.checksum}</code></div><div class="audit-item"><label>Actor</label><code>${latest.actor}</code></div><div class="audit-item"><label>Trigger</label><code>${latest.trigger_type}</code></div>` : `<div class="empty">执行计算后显示 CalculationRun 和 Snapshot。</div>`;
      $("refs").innerHTML = state.input_refs?.length ? `<div class="eyebrow">Frozen input refs</div>${state.input_refs.map((ref) => `<div class="ref"><strong>${ref.object_type}</strong> · ${ref.object_id} · rev ${ref.revision}</div>`).join("")}` : "";
      $("events").innerHTML = state.events?.length ? state.events.map((event) => `<div class="event"><strong>${event.event_type}</strong> · ${event.event_id}<br><span>${event.idempotency_key}</span></div>`).join("") : `<div class="empty">尚未记录 QuoteRecalculationRequired。</div>`;
    };
    const refresh = async () => { try { renderState(await api("/api/v1/demo/state")); } catch (error) { setStatus(error.message); } };
    $("reset").onclick = async () => { try { await api("/api/v1/demo/reset", {method:"POST"}); latestRequest = null; setStatus("Demo 数据已初始化，可以运行初次计算。", "success"); renderResult(null); await refresh(); } catch (error) { setStatus(error.message, "error"); } };
    $("calculate").onclick = async () => { try { latestRequest = requestFor(1); const result = await api("/api/v1/demo/events/quote-recalculation", {method:"POST", body:JSON.stringify(latestRequest)}); renderResult(result.result); setStatus(`V1 已生成 · 总成本 ${money(result.result.total_cost)}`, "success"); await refresh(); } catch (error) { setStatus(error.message, "error"); } };
    $("recalculate").onclick = async () => { try { latestRequest = requestFor(2); const result = await api("/api/v1/demo/events/quote-recalculation", {method:"POST", body:JSON.stringify(latestRequest)}); renderResult(result.result); setStatus(`V2 已生成 · 旧结果 ${result.result.previous_result_id} 保留`, "success"); await refresh(); } catch (error) { setStatus(error.message, "error"); } };
    $("replay").onclick = async () => { try { if (!latestRequest) latestRequest = requestFor(2); const result = await api("/api/v1/demo/replay", {method:"POST", body:JSON.stringify(latestRequest)}); setStatus(result.replayed ? `Replay accepted · ${result.result.result_id} 未重复生成` : "事件已处理", "success"); await refresh(); } catch (error) { setStatus(error.message, "error"); } };
  </script>
</body>
</html>'''
