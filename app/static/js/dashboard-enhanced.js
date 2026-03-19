document.addEventListener("DOMContentLoaded", () => {
  const startDateInput = document.getElementById("start-date");
  const endDateInput = document.getElementById("end-date");
  const filtersForm = document.getElementById("dashboard-filters");
  const resetButton = document.getElementById("reset-dashboard-filters");
  const rangeChip = document.getElementById("dashboard-range-chip");

  const chartPalette = () => {
    const darkMode = document.documentElement.dataset.resolvedTheme === "dark";
    return {
      text: darkMode ? "#d5def5" : "#566a7f",
      border: darkMode ? "rgba(213, 222, 245, 0.14)" : "#e7e7ff",
      fill: darkMode ? "#162033" : "#ffffff",
      imports: "#5b7cff",
      exports: "#28c76f",
      sales: "#00cfe8",
      accent: "#ff9f43"
    };
  };

  let tradeTrendChart;
  let categoryChart;
  let comparisonChart;

  const updateMetrics = (data) => {
    document.querySelector("#metric-imports").textContent = window.appUtils.currency(data.metrics.imports);
    document.querySelector("#metric-exports").textContent = window.appUtils.currency(data.metrics.exports);
    document.querySelector("#metric-sales").textContent = window.appUtils.currency(data.metrics.sales);
    document.querySelector("#metric-average-ticket").textContent = window.appUtils.currency(data.metrics.average_ticket);
    document.querySelector("#metric-products").textContent = data.metrics.products;
    document.querySelector("#metric-users").textContent = data.metrics.users;
    document.querySelector("#metric-active-products").textContent = data.metrics.active_products;
    document.querySelector("#metric-transactions").textContent = data.metrics.transactions;
    document.querySelector("#metric-inventory-units").textContent = data.metrics.inventory_units;
    document.querySelector("#metric-market-coverage").textContent = data.metrics.market_coverage;
  };

  const renderTradeTrend = (data) => {
    const palette = chartPalette();
    tradeTrendChart?.destroy();
    tradeTrendChart = new ApexCharts(document.querySelector("#tradeTrendChart"), {
      chart: {
        height: 350,
        type: "line",
        stacked: false,
        toolbar: { show: false },
        foreColor: palette.text,
        animations: { enabled: true, easing: "easeinout", speed: 900, dynamicAnimation: { speed: 520 } }
      },
      series: [
        { name: "Imports", type: "column", data: data.revenue_series.imports },
        { name: "Exports", type: "column", data: data.revenue_series.exports },
        { name: "Sales", type: "area", data: data.revenue_series.sales }
      ],
      stroke: { width: [0, 0, 3], curve: "smooth" },
      fill: {
        type: ["solid", "solid", "gradient"],
        gradient: { shadeIntensity: 0.35, opacityFrom: 0.4, opacityTo: 0.08, stops: [0, 90, 100] }
      },
      dataLabels: { enabled: false },
      colors: [palette.imports, palette.exports, palette.sales],
      xaxis: {
        categories: data.revenue_series.categories,
        axisBorder: { color: palette.border },
        axisTicks: { color: palette.border }
      },
      yaxis: { labels: { formatter: (value) => window.appUtils.currency(value) } },
      grid: { borderColor: palette.border, strokeDashArray: 5 },
      legend: { position: "top", horizontalAlign: "left" },
      plotOptions: { bar: { borderRadius: 10, columnWidth: "42%" } },
      tooltip: { shared: true, y: { formatter: (value) => window.appUtils.currency(value) } }
    });
    tradeTrendChart.render();
  };

  const renderCategoryChart = (data) => {
    const palette = chartPalette();
    categoryChart?.destroy();
    categoryChart = new ApexCharts(document.querySelector("#categoryBreakdownChart"), {
      chart: {
        type: "donut",
        height: 280,
        foreColor: palette.text,
        animations: { enabled: true, easing: "easeinout", speed: 950, animateGradually: { enabled: true, delay: 90 } }
      },
      series: data.category_breakdown.series.length ? data.category_breakdown.series : [1],
      labels: data.category_breakdown.labels.length ? data.category_breakdown.labels : ["No data"],
      legend: { position: "bottom" },
      colors: [palette.imports, palette.exports, palette.sales, palette.accent, "#7367f0"],
      stroke: { colors: [palette.fill] },
      dataLabels: { enabled: false },
      plotOptions: {
        pie: {
          donut: {
            size: "72%",
            labels: {
              show: true,
              total: {
                show: true,
                label: "Units",
                formatter: () => String(data.metrics.inventory_units)
              }
            }
          }
        }
      }
    });
    categoryChart.render();
  };

  const renderComparisonChart = (data) => {
    const palette = chartPalette();
    comparisonChart?.destroy();
    comparisonChart = new ApexCharts(document.querySelector("#comparisonLineChart"), {
      chart: {
        type: "line",
        height: 320,
        toolbar: { show: false },
        foreColor: palette.text,
        animations: { enabled: true, easing: "easeinout", speed: 850, dynamicAnimation: { speed: 500 } }
      },
      series: [
        { name: "Current Period", data: data.comparison_series.current_period },
        { name: "Previous Year", data: data.comparison_series.previous_year }
      ],
      xaxis: {
        categories: data.comparison_series.categories,
        axisBorder: { color: palette.border },
        axisTicks: { color: palette.border }
      },
      stroke: { width: 3, curve: "smooth" },
      colors: [palette.imports, palette.accent],
      markers: { size: 5, strokeWidth: 0, hover: { size: 7 } },
      grid: { borderColor: palette.border, strokeDashArray: 5 },
      legend: { position: "top", horizontalAlign: "left" },
      tooltip: { y: { formatter: (value) => window.appUtils.currency(value) } },
      yaxis: { labels: { formatter: (value) => window.appUtils.currency(value) } }
    });
    comparisonChart.render();
  };

  const renderActivity = (rows) => {
    const activityRoot = document.querySelector("#recent-activity");
    if (!rows.length) {
      activityRoot.innerHTML = '<div class="empty-state py-4">No trade activity found for the selected date range.</div>';
      return;
    }

    activityRoot.innerHTML = rows
      .map(
        (row) => `
        <div class="activity-row">
          <div>
            <h6 class="mb-1">${row.product}</h6>
            <small class="text-muted">${row.type} • Qty ${row.quantity}</small>
          </div>
          <div class="text-end">
            <strong>${window.appUtils.currency(row.amount)}</strong>
            <small class="text-muted d-block">${row.date}</small>
          </div>
        </div>`
      )
      .join("");
  };

  const updateFilters = (filters) => {
    startDateInput.min = filters.available_start_date;
    startDateInput.max = filters.available_end_date;
    endDateInput.min = filters.available_start_date;
    endDateInput.max = filters.available_end_date;
    startDateInput.value = filters.start_date;
    endDateInput.value = filters.end_date;
    rangeChip.textContent = `${window.appUtils.formatDate(filters.start_date)} - ${window.appUtils.formatDate(filters.end_date)}`;
  };

  const loadDashboard = async () => {
    const params = new URLSearchParams();
    if (startDateInput.value) params.set("start_date", startDateInput.value);
    if (endDateInput.value) params.set("end_date", endDateInput.value);
    const query = params.toString();
    const data = await window.appUtils.json(`/api/dashboard${query ? `?${query}` : ""}`);

    updateMetrics(data);
    updateFilters(data.filters);
    renderTradeTrend(data);
    renderCategoryChart(data);
    renderComparisonChart(data);
    renderActivity(data.recent_activity);
  };

  filtersForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    await loadDashboard();
  });

  resetButton.addEventListener("click", async () => {
    startDateInput.value = "";
    endDateInput.value = "";
    await loadDashboard();
  });

  window.addEventListener("theme:changed", () => {
    loadDashboard();
  });

  loadDashboard();
});
