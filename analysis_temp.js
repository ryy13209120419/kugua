// ===== AI 市场分析 (adapted for direct API use + callAiApi) =====
var AI_HISTORY_KEY_MARKET = "tradelens_market_v2";

async function refreshAIAnalysis() {
  var btn = document.getElementById("ai-refresh-btn");
  if (!btn) return;
  btn.disabled = true;
  btn.textContent = "⏳";
  showSectionLoading("ai-overview");
  showSectionLoading("ai-trend");
  showSectionLoading("ai-volatility");
  showSectionLoading("ai-opportunity");
  showSectionLoading("ai-levels");
  try {
    var data = await fetchMarketDataDirect();
    renderMarketSources(data);
    renderMarketOverview(data);
    btn.textContent = "🧠";
    var analysis = await runMarketAIAnalysis(data);
    if (analysis) {
      renderAIAnalysis(analysis);
      saveMarketHistory(analysis);
      renderMarketHistory();
      showToast("分析完成", "success");
    } else {
      showNoMarketAI();
    }
  } catch(e) {
    showToast("分析出错", "error");
  }
  btn.disabled = false;
  btn.textContent = "🔄 刷新分析";
}

async function fetchMarketDataDirect() {
  var result = { sources: [], ts: new Date().toISOString() };
  try {
    var r = await fetch("https://api.binance.com/api/v3/ticker/24hr?symbols=[%22BTCUSDT%22,%22ETHUSDT%22,%22BNBUSDT%22,%22SOLUSDT%22,%22XRPUSDT%22,%22DOGEUSDT%22,%22ADAUSDT%22,%22AVAXUSDT%22,%22DOTUSDT%22,%22LINKUSDT%22]");
    if (r.ok) { var j = await r.json(); if (Array.isArray(j)) result.binance = j; result.sources.push("Binance"); }
  } catch(e) {}
  try { var r2 = await fetch("https://api.alternative.me/fng/?limit=1"); if (r2.ok) { var j2 = await r2.json(); if (j2.data) result.fearGreed = j2.data[0]; result.sources.push("FearGreed"); } } catch(e) {}
  return result;
}

function renderMarketSources(data) {
  var div = document.getElementById("ai-sources");
  if (!div) return;
  var time = new Date().toLocaleString("zh-CN");
  var srcs = data.sources.length > 0 ? data.sources.join(" | ") : "(离线)";
  var marketLabel = '';
  try { if (typeof selectedMarket !== 'undefined' && selectedMarket) {
    var mktNames = { 'crypto': '加密货币', 'us_stocks': '美股', 'gold': '黄金', 'futures': '期货' };
    marketLabel = ' | 聚焦: <strong>' + (mktNames[selectedMarket] || selectedMarket) + '</strong>';
  } } catch(e) {}
  div.innerHTML = "<span style=\"color:var(--accent)\">" + time + "</span> 数据源: " + srcs + marketLabel;
}
function fmtNum(n) {
  if (!n) return "0";
  if (n >= 1e12) return (n/1e12).toFixed(2)+"T";
  if (n >= 1e9) return (n/1e9).toFixed(2)+"B";
  if (n >= 1e6) return (n/1e6).toFixed(2)+"M";
  if (n >= 1e3) return (n/1e3).toFixed(2)+"K";
  return n.toFixed(2);
}

function renderMarketOverview(data) {
  var div = document.getElementById("ai-overview");
  var time = document.getElementById("ai-time");
  if (!div) return;
  if (time) time.textContent = new Date().toLocaleString("zh-CN");
  var html = "<div style=\"font-size:13px;line-height:1.8\">";
  html += "<div class=\"stats-grid\" style=\"grid-template-columns:repeat(auto-fill,minmax(140px,1fr))\">";
  if (data.fearGreed) {
    var fv = parseInt(data.fearGreed.value);
    html += "<div class=\"stat-card\"><div class=\"stat-label\">恐惧贪婪</div><div class=\"stat-value\" style=\"font-size:14px;color:" + (fv > 50 ? "var(--profit)" : "var(--loss)") + "\">" + fv + " (" + data.fearGreed.value_classification + ")</div></div>";
  }
  html += "</div>";
  if (data.binance && data.binance.length > 0) {
    html += "<div style=\"margin-top:10px;font-weight:600;font-size:13px;margin-bottom:6px\">主流币实时</div>";
    html += "<div style=\"display:grid;grid-template-columns:repeat(auto-fill,minmax(140px,1fr));gap:6px\">";
    for (var bi = 0; bi < data.binance.length; bi++) {
      var t = data.binance[bi];
      var chg = parseFloat(t.priceChangePercent);
      html += "<div style=\"background:var(--bg3);padding:8px;border-radius:var(--radius-sm);font-size:12px\"><div style=\"font-weight:600\">" + t.symbol.replace("USDT","") + "</div><div style=\"color:var(--text2)\">$" + parseFloat(t.lastPrice).toFixed(5) + "</div><div style=\"color:" + (chg>=0?"var(--profit)":"var(--loss)") + ";font-weight:600\">" + (chg>=0?"+":"") + chg.toFixed(2) + "%</div></div>";
    }
    html += "</div>";
  }
  if (!data.binance && !data.fearGreed) html += "<div style=\"text-align:center;padding:24px;color:var(--text3);font-size:13px\">无法获取实时数据</div>";
  html += "</div>";
  div.innerHTML = html;
}

async function runMarketAIAnalysis(data) {
  var ak = null;
  try { ak = settings.aiApiKey; } catch(e) {}
  if (!ak) return null;
  var marketFocus = '';
  try { if (typeof selectedMarket !== 'undefined' && selectedMarket) {
    var mktNames = { 'crypto': '加密货币', 'us_stocks': '美股', 'gold': '黄金', 'futures': '期货' };
    marketFocus = '当前分析聚焦于: ' + (mktNames[selectedMarket] || selectedMarket) + '\n请专注分析该市场的数据、走势、机会与风险。\n\n';
  } } catch(e) {}
  var prompt = "你是一位专业的金融市场分析师。请基于以下实时市场数据，生成一份完整的市场分析报告。\n\n## 市场数据\n\n";
  prompt += marketFocus;prompt += "\n请按以下五个板块输出分析（使用中文，每个板块保留emoji标题）：\n\n📊 大盘概况\n\n📈 走势预测\n\n⚡ 异动监测\n\n🎯 机会提示\n\n📋 具体点位与建议\n\n要求：内容简洁具体，关键数据加粗，给出明确的支撑/阻力位数值。";
  try { var respText = await callAiApi([{ role: "system", content: "你是一位专业的金融市场分析师" + (marketFocus ? " 聚焦分析: " + marketFocus.replace("\n"," ") : "") }, { role: "user", content: prompt }]); if (respText) return respText; } catch(e) {}
  return null;
}

function renderAIAnalysis(text) {
  if (!text) return;
  var sections = { "📊":"ai-overview", "📈":"ai-trend", "⚡":"ai-volatility", "🎯":"ai-opportunity", "📋":"ai-levels" };
  var emojis = ["📊","📈","⚡","🎯","📋"];
  var parsed = 0;
  for (var ei = 0; ei < emojis.length; ei++) { var em = emojis[ei];
    var sid = sections[em];
    if (!sid) continue;
    var start = text.indexOf(em);
    if (start < 0) continue;
    var end = text.length;
    for (var ej = ei+1; ej < emojis.length; ej++) { var nextIdx = text.indexOf(emojis[ej], start+2); if (nextIdx > start && nextIdx < end) end = nextIdx; }
    var content = text.substring(start, end).trim();
    parsed++;
    var div = document.getElementById(sid);
    if (!div) continue;
    var lines = content.split("\n");
    if (lines[0] && lines[0].match(/^[📊📈⚡🎯📋]/)) lines.shift();
    var body = lines.join("\n").trim();
    body = body.replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>").replace(/\n/g, "<br>").replace(/- /g, "• ");
    div.innerHTML = "<div style=\"font-size:13px;line-height:1.8;color:var(--text2)\">" + body + "</div>";
  }
  if (parsed === 0) {
    var mainDiv = document.getElementById("ai-overview");
    if (mainDiv) mainDiv.innerHTML = "<div style=\"font-size:13px;line-height:1.8;color:var(--text2)\">" + escHtmlSimple(text) + "</div>";
  }
}

function escHtmlSimple(t) { var d = document.createElement("div"); d.textContent = t; return d.innerHTML; }

function showSectionLoading(id) {
  var div = document.getElementById(id);
  if (div) div.innerHTML = "<div style=\"text-align:center;padding:24px;color:var(--text3);font-size:13px\">⏳ 加载中...</div>";
}

function showNoMarketAI() {
  var msg = "AI 分析不可用。请先在设置中配置 API Key。";
  var ids = ["ai-trend","ai-volatility","ai-opportunity","ai-levels"];
  for (var i = 0; i < ids.length; i++) { var d = document.getElementById(ids[i]); if (d) d.innerHTML = "<div style=\"text-align:center;padding:24px;color:var(--text3);font-size:13px\">" + msg + "</div>"; }
}

function saveMarketHistory(text) { try { var h = JSON.parse(localStorage.getItem(AI_HISTORY_KEY_MARKET) || "[]"); h.unshift({ id: Date.now(), ts: new Date().toISOString(), text: text, preview: (text || "").substring(0, 100) }); if (h.length > 20) h.length = 20; localStorage.setItem(AI_HISTORY_KEY_MARKET, JSON.stringify(h)); } catch(e) {} }

function renderMarketHistory() {
  var div = document.getElementById("ai-history");
  if (!div) return;
  try { var h = JSON.parse(localStorage.getItem(AI_HISTORY_KEY_MARKET) || "[]"); if (h.length === 0) { div.innerHTML = "<div style=\"text-align:center;padding:24px;color:var(--text3);font-size:13px\">暂无记录</div>"; return; } var html = ""; for (var i = 0; i < h.length; i++) { var item = h[i]; var t = new Date(item.ts).toLocaleString("zh-CN"); html += "<div class=\"settings-row\" style=\"cursor:pointer\" onclick=\"viewMarketHistory(" + i + ")\"><div style=\"flex:1\"><div style=\"font-size:12px;font-weight:600\">" + t + "</div><div style=\"font-size:11px;color:var(--text3);margin-top:2px\">" + escHtmlSimple(item.preview || "") + "...</div></div><div>></div></div>"; } div.innerHTML = html; } catch(e) { div.innerHTML = "<div style=\"text-align:center;padding:24px;color:var(--text3)\">加载失败</div>"; }
}

function viewMarketHistory(idx) {
  try { var h = JSON.parse(localStorage.getItem(AI_HISTORY_KEY_MARKET) || "[]"); if (idx >= 0 && idx < h.length) { renderAIAnalysis(h[idx].text); var time = document.getElementById("ai-time"); if (time) time.textContent = "历史: " + new Date(h[idx].ts).toLocaleString("zh-CN"); showToast("已加载历史分析", "info"); } } catch(e) {}
}

function clearMarketHistory() {
  if (confirm("确定清空所有分析历史？")) { localStorage.removeItem(AI_HISTORY_KEY_MARKET); renderMarketHistory(); showToast("已清空", "info"); }
}
