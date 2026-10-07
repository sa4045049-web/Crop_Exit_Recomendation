
let lastResult = null;

document.querySelectorAll(".tab").forEach(btn => {
  btn.addEventListener("click", () => {
    document.querySelectorAll(".tab").forEach(x => x.classList.remove("active"));
    document.querySelectorAll(".tab-panel").forEach(x => x.classList.remove("active"));
    btn.classList.add("active");
    document.getElementById(btn.dataset.tab).classList.add("active");
  });
});

document.getElementById("crop").addEventListener("change", async (e) => {
  const data = await fetch("/api/crops").then(r => r.json());
  const p = data[e.target.value];
  if (p) document.getElementById("current_price").value = p.base_price;
});

function money(n){ return "₹" + Number(n).toLocaleString("en-IN"); }

async function analyze(){
  const payload = {
    crop: document.getElementById("crop").value,
    area: document.getElementById("area").value,
    current_price: document.getElementById("current_price").value,
    days_left: document.getElementById("days_left").value,
    rainfall_risk: document.getElementById("rainfall_risk").value,
    temp_risk: document.getElementById("temp_risk").value,
    extra_cost: document.getElementById("extra_cost").value,
    storage_months: document.getElementById("storage_months").value
  };
  const res = await fetch("/api/analyze", {method:"POST", headers:{"Content-Type":"application/json"}, body:JSON.stringify(payload)});
  const data = await res.json();
  if(data.error){ alert(data.error); return; }
  lastResult = data;
  document.getElementById("emptyState").classList.add("hidden");
  document.getElementById("result").classList.remove("hidden");
  document.getElementById("decision").textContent = data.decision;
  document.getElementById("confidence").textContent = data.confidence + "%";
  document.getElementById("risk").textContent = data.risk + " " + data.risk_label;
  document.getElementById("futurePrice").textContent = money(data.future_price);
  document.getElementById("futureProfit").textContent = money(data.future_profit);
  document.getElementById("breakEven").textContent = money(data.break_even);
  document.getElementById("revNow").textContent = money(data.revenue_now);
  document.getElementById("futureRev").textContent = money(data.future_revenue);
  document.getElementById("profitNow").textContent = money(data.now_profit);
  document.getElementById("profitFuture").textContent = money(data.future_profit);
  document.getElementById("margin").textContent = data.profit_margin + "%";
  document.getElementById("movement").textContent = (data.price_trend_pct >= 0 ? "+" : "") + data.price_trend_pct + "%";
  document.getElementById("reasons").innerHTML = data.reasons.map(x => `<li>${x}</li>`).join("");
  renderChart(data);
  document.getElementById("scenarioGrid").innerHTML = data.scenarios.map(s => `
    <div class="scenario"><h3>${s.label}</h3><div class="price">Estimated price · ${money(s.price)}</div>
    <div class="profit">${money(s.profit)}</div><div class="price">estimated profit</div></div>`).join("");
  document.querySelector('[data-tab="decision"]').click();
}

function renderChart(data){
  const canvas = document.getElementById("priceChart");
  const ctx = canvas.getContext("2d");
  const w = canvas.clientWidth * (window.devicePixelRatio || 1);
  const h = canvas.clientHeight * (window.devicePixelRatio || 1);
  canvas.width = w; canvas.height = h;
  ctx.clearRect(0,0,w,h);
  const values = [data.current_price, ...data.forecast];
  const min = Math.min(...values) * 0.97;
  const max = Math.max(...values) * 1.03;
  const pad = 34;
  const x = i => pad + i * ((w - 2*pad) / (values.length-1));
  const y = v => h-pad - ((v-min)/(max-min))*(h-2*pad);
  ctx.font = `${11*(window.devicePixelRatio||1)}px Arial`;
  ctx.lineWidth = 3*(window.devicePixelRatio||1);
  ctx.strokeStyle = "#3157d5";
  ctx.beginPath();
  values.forEach((v,i)=> i ? ctx.lineTo(x(i),y(v)) : ctx.moveTo(x(i),y(v)));
  ctx.stroke();
  values.forEach((v,i)=>{ctx.fillStyle="#1fa7a0";ctx.beginPath();ctx.arc(x(i),y(v),4*(window.devicePixelRatio||1),0,Math.PI*2);ctx.fill();});
  ctx.fillStyle="#667085";
  ["Current","+1 month","+2 months","+3 months"].forEach((lab,i)=>ctx.fillText(lab,x(i)-22*(window.devicePixelRatio||1),h-10*(window.devicePixelRatio||1)));
}


async function compareCrops(){
  const selected = [...document.getElementById("compareCrops").selectedOptions].map(o=>o.value).slice(0,4);
  if(selected.length < 2){ alert("Select at least 2 crops."); return; }
  const area = document.getElementById("compareArea").value;
  const res = await fetch("/api/compare",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({crops:selected,area})});
  const rows = await res.json();
  document.getElementById("compareTable").innerHTML = `
  <table><thead><tr><th>Crop</th><th>Future price</th><th>Revenue</th><th>Future profit</th><th>Risk</th><th>Decision</th></tr></thead>
  <tbody>${rows.map((r,i)=>`<tr><td><b>${i===0?"★ ":""}${r.crop}</b></td><td>${money(r.future_price)}</td><td>${money(r.future_revenue)}</td><td>${money(r.future_profit)}</td><td>${r.risk_label}</td><td>${r.decision}</td></tr>`).join("")}</tbody></table>`;
}
