document.addEventListener("DOMContentLoaded", async () => {
  const data = await window.appUtils.json("/api/dashboard");

  document.querySelector("#metric-imports").textContent = window.appUtils.currency(data.metrics.imports);
  document.querySelector("#metric-exports").textContent = window.appUtils.currency(data.metrics.exports);
  document.querySelector("#metric-sales").textContent = window.appUtils.currency(data.metrics.sales);
  document.querySelector("#metric-products").textContent = data.metrics.products;
  document.querySelector("#metric-users").textContent = data.metrics.users;
  document.querySelector("#metric-active-products").textContent = data.metrics.active_products;

  new ApexCharts(document.querySelector("#tradeTrendChart"), {
    chart: { type: "bar", height: 320, toolbar: { show: false } },
    series: [
      { name: "Imports", data: data.revenue_series.imports },
      { name: "Exports", data: data.revenue_series.exports },
      { name: "Sales", data: data.revenue_series.sales }
    ],
    xaxis: { categories: data.revenue_series.categories },
    colors: ["#696cff", "#71dd37", "#03c3ec"],
    plotOptions: { bar: { borderRadius: 8, columnWidth: "45%" } }
  }).render();

  new ApexCharts(document.querySelector("#categoryBreakdownChart"), {
    chart: { type: "donut", height: 220 },
    series: data.category_breakdown.series,
    labels: data.category_breakdown.labels,
    legend: { position: "bottom" },
    colors: ["#696cff", "#8592a3", "#03c3ec", "#ffab00", "#71dd37"]
  }).render();

  document.querySelector("#recent-activity").innerHTML = data.recent_activity
    .map(
      (row) => `
      <div class="list-group-item px-0">
        <div class="d-flex justify-content-between">
          <div>
            <h6 class="mb-1">${escapeHtml(row.product)}</h6>
            <small class="text-muted">${escapeHtml(row.type)} • Qty ${escapeHtml(row.quantity)}</small>
          </div>
          <div class="text-end">
            <strong>${window.appUtils.currency(row.amount)}</strong>
            <small class="text-muted d-block">${escapeHtml(row.date)}</small>
          </div>
        </div>
      </div>`
    )
    .join("");
});
