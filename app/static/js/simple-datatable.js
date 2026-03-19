(function () {
  class SimpleDataTable {
    constructor(options) {
      this.tableBody = document.querySelector(options.tableBodySelector);
      this.paginationContainer = document.querySelector(options.paginationSelector);
      this.searchInput = document.querySelector(options.searchSelector);
      this.fetchData = options.fetchData;
      this.renderRow = options.renderRow;
      this.afterRender = options.afterRender;
      this.emptyColumns = options.emptyColumns || 10;
      this.pageSize = options.pageSize || 8;
      this.rows = [];
      this.filteredRows = [];
      this.currentPage = 1;

      if (this.searchInput) {
        this.searchInput.addEventListener("input", () => {
          this.currentPage = 1;
          this.applySearch();
          this.render();
        });
      }
    }

    async reload() {
      this.rows = await this.fetchData(this.searchInput ? this.searchInput.value : "");
      this.applySearch();
      this.render();
    }

    applySearch() {
      const query = (this.searchInput?.value || "").trim().toLowerCase();
      this.filteredRows = !query
        ? [...this.rows]
        : this.rows.filter((row) => JSON.stringify(row).toLowerCase().includes(query));
    }

    render() {
      const start = (this.currentPage - 1) * this.pageSize;
      const pageRows = this.filteredRows.slice(start, start + this.pageSize);

      if (!pageRows.length) {
        this.tableBody.innerHTML = `<tr><td colspan="${this.emptyColumns}"><div class="empty-state">No records found.</div></td></tr>`;
      } else {
        this.tableBody.innerHTML = pageRows.map(this.renderRow).join("");
      }

      this.renderPagination();
      if (window.appUtils?.enhanceDynamicUI) {
        window.appUtils.enhanceDynamicUI();
      }
      if (typeof this.afterRender === "function") {
        this.afterRender(pageRows, this.filteredRows);
      }
    }

    renderPagination() {
      const totalPages = Math.max(1, Math.ceil(this.filteredRows.length / this.pageSize));
      this.currentPage = Math.min(this.currentPage, totalPages);
      this.paginationContainer.innerHTML = `
        <div class="datatable-pagination">
          <small class="text-muted">Showing ${this.filteredRows.length ? (this.currentPage - 1) * this.pageSize + 1 : 0} to ${Math.min(this.currentPage * this.pageSize, this.filteredRows.length)} of ${this.filteredRows.length} entries</small>
          <div class="btn-group">
            <button class="btn btn-outline-primary btn-sm" ${this.currentPage === 1 ? "disabled" : ""} data-role="prev">Previous</button>
            <button class="btn btn-outline-primary btn-sm" ${this.currentPage === totalPages ? "disabled" : ""} data-role="next">Next</button>
          </div>
        </div>
      `;

      this.paginationContainer.querySelector('[data-role="prev"]')?.addEventListener("click", () => {
        if (this.currentPage > 1) {
          this.currentPage -= 1;
          this.render();
        }
      });
      this.paginationContainer.querySelector('[data-role="next"]')?.addEventListener("click", () => {
        if (this.currentPage < totalPages) {
          this.currentPage += 1;
          this.render();
        }
      });
    }
  }

  window.SimpleDataTable = SimpleDataTable;
})();
