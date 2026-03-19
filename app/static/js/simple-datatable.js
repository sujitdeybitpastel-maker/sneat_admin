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

    goToPage(page) {
      const totalPages = Math.max(1, Math.ceil(this.filteredRows.length / this.pageSize));
      this.currentPage = Math.max(1, Math.min(page, totalPages));
      this.render();
    }

    getPageNumbers(currentPage, totalPages) {
      const pages = [];
      const maxVisible = 5;

      if (totalPages <= maxVisible + 2) {
        for (let i = 1; i <= totalPages; i++) pages.push(i);
        return pages;
      }

      pages.push(1);

      let start = Math.max(2, currentPage - 1);
      let end = Math.min(totalPages - 1, currentPage + 1);

      if (currentPage <= 3) {
        start = 2;
        end = Math.min(maxVisible, totalPages - 1);
      } else if (currentPage >= totalPages - 2) {
        start = Math.max(2, totalPages - maxVisible + 1);
        end = totalPages - 1;
      }

      if (start > 2) pages.push("...");
      for (let i = start; i <= end; i++) pages.push(i);
      if (end < totalPages - 1) pages.push("...");

      pages.push(totalPages);
      return pages;
    }

    renderPagination() {
      const totalPages = Math.max(1, Math.ceil(this.filteredRows.length / this.pageSize));
      this.currentPage = Math.min(this.currentPage, totalPages);

      const startEntry = this.filteredRows.length ? (this.currentPage - 1) * this.pageSize + 1 : 0;
      const endEntry = Math.min(this.currentPage * this.pageSize, this.filteredRows.length);
      const totalEntries = this.filteredRows.length;

      const pageNumbers = this.getPageNumbers(this.currentPage, totalPages);

      let pageButtonsHtml = "";
      pageNumbers.forEach((p) => {
        if (p === "...") {
          pageButtonsHtml += `<span class="btn btn-sm btn-outline-secondary pagination-ellipsis" disabled>...</span>`;
        } else {
          const isActive = p === this.currentPage;
          pageButtonsHtml += `<button class="btn btn-sm ${isActive ? "btn-primary" : "btn-outline-primary"} pagination-page-btn" data-page="${p}" ${isActive ? 'aria-current="page"' : ""}>${p}</button>`;
        }
      });

      this.paginationContainer.innerHTML = `
        <div class="datatable-pagination">
          <small class="text-muted">Showing ${startEntry}\u2013${endEntry} of ${totalEntries}</small>
          <div class="pagination-controls">
            <button class="btn btn-outline-primary btn-sm pagination-nav-btn" ${this.currentPage === 1 ? "disabled" : ""} data-role="prev" aria-label="Previous page">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="m15 18-6-6 6-6"/></svg>
            </button>
            <div class="pagination-pages">${pageButtonsHtml}</div>
            <button class="btn btn-outline-primary btn-sm pagination-nav-btn" ${this.currentPage === totalPages ? "disabled" : ""} data-role="next" aria-label="Next page">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="m9 18 6-6-6-6"/></svg>
            </button>
          </div>
        </div>
      `;

      this.paginationContainer.querySelector('[data-role="prev"]')?.addEventListener("click", () => {
        if (this.currentPage > 1) this.goToPage(this.currentPage - 1);
      });
      this.paginationContainer.querySelector('[data-role="next"]')?.addEventListener("click", () => {
        if (this.currentPage < totalPages) this.goToPage(this.currentPage + 1);
      });
      this.paginationContainer.querySelectorAll(".pagination-page-btn").forEach((btn) => {
        btn.addEventListener("click", () => {
          this.goToPage(parseInt(btn.dataset.page, 10));
        });
      });
    }
  }

  window.SimpleDataTable = SimpleDataTable;
})();
