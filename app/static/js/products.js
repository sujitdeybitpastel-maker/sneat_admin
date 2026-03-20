document.addEventListener("DOMContentLoaded", () => {
  const page = document.getElementById("products-page");
  const canMainEdit = page?.dataset.canMainEdit === "true";
  const canManageUpdates = page?.dataset.canManageUpdates === "true";
  const activeSection = page?.dataset.activeSection || "main";
  const selectedProductIds = new Set();
  const selectAllCheckbox = document.getElementById("products-select-all");

  const productModalElement = document.getElementById("productModal");
  const productModal = productModalElement ? new bootstrap.Modal(productModalElement) : null;
  const productUpdatesModalElement = document.getElementById("productUpdatesModal");
  const productUpdatesModal = productUpdatesModalElement ? new bootstrap.Modal(productUpdatesModalElement) : null;

  const productForm = document.getElementById("product-form");
  const supervisorForm = document.getElementById("supervisor-update-form");
  const productFields = ["sku", "name", "category", "unit_price", "quantity", "origin_country", "destination_country"];

  if (productForm) {
    window.appUtils.attachValidationCleanup(productForm);
  }
  if (supervisorForm) {
    window.appUtils.attachValidationCleanup(supervisorForm);
  }

  const productValidationRules = {
    sku: [window.appUtils.validators.required("SKU"), window.appUtils.validators.minLength("SKU", 4)],
    name: [window.appUtils.validators.required("Product name"), window.appUtils.validators.minLength("Product name", 3)],
    category: [window.appUtils.validators.required("Category"), window.appUtils.validators.minLength("Category", 2)],
    unit_price: [window.appUtils.validators.required("Unit price"), window.appUtils.validators.positiveNumber("Unit price")],
    quantity: [window.appUtils.validators.required("Base quantity"), window.appUtils.validators.nonNegativeInteger("Base quantity")],
    origin_country: [window.appUtils.validators.required("Origin country"), window.appUtils.validators.minLength("Origin country", 2)],
    destination_country: [window.appUtils.validators.required("Destination country"), window.appUtils.validators.minLength("Destination country", 2)]
  };

  const supervisorValidationRules = {
    "supervisor-product-id": [window.appUtils.validators.required("Product")],
    "supervisor-quantity-delta": [window.appUtils.validators.required("Quantity change")]
  };

  const mainTable = new SimpleDataTable({
    tableBodySelector: "#products-table tbody",
    paginationSelector: "#products-pagination",
    searchSelector: "#products-search",
    emptyColumns: 11,
    fetchData: async () => window.appUtils.json("/products/api"),
    renderRow: (row) => {
      const adjustmentLabel = row.supervisor_quantity_delta === 0
        ? "No supervisor change"
        : `${row.supervisor_quantity_delta > 0 ? "+" : ""}${row.supervisor_quantity_delta} supervisor`;
      const actions = [
        `<button class="btn btn-sm btn-outline-secondary me-1" data-action="view" data-id="${row.id}">${window.appUtils.icon("eye", "me-1")}View</button>`
      ];
      if (canMainEdit) {
        actions.unshift(`<button class="btn btn-sm btn-outline-primary me-1" data-action="edit" data-id="${row.id}">${window.appUtils.icon("edit", "me-1")}Edit</button>`);
      }

      return `
        <tr>
          <td class="text-center"><input class="form-check-input product-row-checkbox" type="checkbox" data-id="${row.id}" ${selectedProductIds.has(String(row.id)) ? "checked" : ""} aria-label="Select product ${escapeHtml(row.name)}" /></td>
          <td>${escapeHtml(row.sku)}</td>
          <td><strong>${escapeHtml(row.name)}</strong></td>
          <td>${escapeHtml(row.category)}</td>
          <td>${escapeHtml(row.origin_country)}</td>
          <td>${escapeHtml(row.destination_country)}</td>
          <td>${window.appUtils.currency(row.unit_price)}</td>
          <td>
            <strong>${escapeHtml(row.quantity)}</strong><br />
            <small class="text-muted">Base ${escapeHtml(row.base_quantity)} | ${escapeHtml(adjustmentLabel)}</small>
          </td>
          <td>${window.appUtils.badge(row.status)}</td>
          <td>
            ${escapeHtml(row.updated_at)}<br />
            <small class="text-muted">${escapeHtml(row.updated_by)}</small>
          </td>
          <td>${actions.join("")}</td>
        </tr>`;
    },
    afterRender: (_pageRows, filteredRows) => {
      const ids = filteredRows.map((row) => String(row.id));
      const allSelected = ids.length > 0 && ids.every((id) => selectedProductIds.has(id));
      const someSelected = ids.some((id) => selectedProductIds.has(id));
      if (selectAllCheckbox) {
        selectAllCheckbox.checked = allSelected;
        selectAllCheckbox.indeterminate = !allSelected && someSelected;
      }
    }
  });

  const supervisorTable = canManageUpdates && document.querySelector("#supervisor-updates-table tbody")
    ? new SimpleDataTable({
        tableBodySelector: "#supervisor-updates-table tbody",
        paginationSelector: "#supervisor-updates-pagination",
        searchSelector: "#supervisor-updates-search",
        emptyColumns: 5,
        fetchData: async () => window.appUtils.json("/products/api/supervisor/updates"),
        renderRow: (row) => `
          <tr>
            <td><strong>${escapeHtml(row.product_name)}</strong><br /><small class="text-muted">${escapeHtml(row.product_sku)}</small></td>
            <td>${row.quantity_delta > 0 ? "+" : ""}${escapeHtml(row.quantity_delta)}</td>
            <td>${escapeHtml(row.remarks || "-")}</td>
            <td>${escapeHtml(row.updated_by)}</td>
            <td>${escapeHtml(row.created_at)}</td>
          </tr>`
      })
    : null;

  const populateSupervisorProducts = () => {
    if (!canManageUpdates) return;
    const select = document.getElementById("supervisor-product-id");
    if (!select) return;

    const selectedValue = select.value;
    select.innerHTML = '<option value="">Select a product</option>' + mainTable.rows
      .filter((row) => String(row.status).toLowerCase() !== "inactive")
      .map((row) => `<option value="${row.id}">${escapeHtml(row.sku)} - ${escapeHtml(row.name)} (Qty ${escapeHtml(row.quantity)})</option>`)
      .join("");
    select.value = selectedValue;
  };

  const resetProductForm = () => {
    if (!productForm) return;
    productForm.reset();
    window.appUtils.clearFormErrors(productForm);
    document.getElementById("product-id").value = "";
    document.getElementById("product-modal-title").textContent = "Add Product";
  };

  document.getElementById("add-product-btn")?.addEventListener("click", resetProductForm);
  document.getElementById("download-products-btn")?.addEventListener("click", () => {
    const ids = Array.from(selectedProductIds);
    const query = ids.length ? `?ids=${ids.join(",")}` : "";
    window.location.href = `/products/api/export${query}`;
  });

  selectAllCheckbox?.addEventListener("change", () => {
    const visibleIds = mainTable.filteredRows.map((row) => String(row.id));
    if (selectAllCheckbox.checked) {
      visibleIds.forEach((id) => selectedProductIds.add(id));
    } else {
      visibleIds.forEach((id) => selectedProductIds.delete(id));
    }
    mainTable.render();
  });

  productForm?.addEventListener("submit", async (event) => {
    event.preventDefault();
    if (!window.appUtils.validateForm(productForm, productValidationRules)) {
      return;
    }

    const id = document.getElementById("product-id").value;
    const payload = Object.fromEntries(productFields.map((field) => [field, document.getElementById(field).value]));

    try {
      await window.appUtils.json(id ? `/products/api/${id}` : "/products/api", {
        method: id ? "PUT" : "POST",
        body: JSON.stringify(payload)
      });
      productModal?.hide();
      resetProductForm();
      await mainTable.reload();
      populateSupervisorProducts();
    } catch (error) {
      if (error.fieldErrors && Object.keys(error.fieldErrors).length) {
        window.appUtils.applyBackendErrors(productForm, error.fieldErrors);
        return;
      }
      alert(error.message);
    }
  });

  supervisorForm?.addEventListener("submit", async (event) => {
    event.preventDefault();
    if (!window.appUtils.validateForm(supervisorForm, supervisorValidationRules)) {
      return;
    }

    const payload = {
      product_id: document.getElementById("supervisor-product-id").value,
      quantity_delta: document.getElementById("supervisor-quantity-delta").value,
      remarks: document.getElementById("supervisor-remarks").value
    };

    try {
      await window.appUtils.json("/products/api/supervisor/updates", {
        method: "POST",
        body: JSON.stringify(payload)
      });
      supervisorForm.reset();
      window.appUtils.clearFormErrors(supervisorForm);
      await mainTable.reload();
      populateSupervisorProducts();
      await supervisorTable?.reload();
    } catch (error) {
      if (error.fieldErrors && Object.keys(error.fieldErrors).length) {
        window.appUtils.applyBackendErrors(supervisorForm, error.fieldErrors);
        return;
      }
      alert(error.message);
    }
  });

  document.querySelector("#products-table tbody")?.addEventListener("click", async (event) => {
    const checkbox = event.target.closest(".product-row-checkbox");
    if (checkbox) {
      const id = String(checkbox.dataset.id);
      if (checkbox.checked) {
        selectedProductIds.add(id);
      } else {
        selectedProductIds.delete(id);
      }
      mainTable.render();
      return;
    }

    const button = event.target.closest("button[data-action]");
    if (!button) return;

    const row = mainTable.rows.find((item) => String(item.id) === button.dataset.id);
    if (!row) return;

    if (button.dataset.action === "edit") {
      document.getElementById("product-id").value = row.id;
      document.getElementById("product-modal-title").textContent = "Edit Product";
      productFields.forEach((field) => {
        document.getElementById(field).value = field === "quantity" ? row.base_quantity : row[field];
      });
      productModal?.show();
      return;
    }

    if (button.dataset.action === "view") {
      const payload = await window.appUtils.json(`/products/api/${row.id}/updates`);
      document.getElementById("product-updates-modal-title").textContent = `${payload.product.name} Updates`;
      const tableBody = document.querySelector("#product-updates-table tbody");
      const updates = payload.updates || [];
      tableBody.innerHTML = updates.length
        ? updates.map((item) => `
            <tr>
              <td>${item.quantity_delta > 0 ? "+" : ""}${escapeHtml(item.quantity_delta)}</td>
              <td>${escapeHtml(item.remarks || "-")}</td>
              <td>${escapeHtml(item.updated_by)}</td>
              <td>${escapeHtml(item.created_at)}</td>
            </tr>`).join("")
        : '<tr><td colspan="4"><div class="empty-state">No product updates found for this product.</div></td></tr>';
      productUpdatesModal?.show();
    }
  });

  const initialize = async () => {
    const activeTabButton = document.querySelector(
      activeSection === "supervisor" ? "#products-supervisor-tab" : "#products-main-tab"
    );
    activeTabButton?.click();
    await mainTable.reload();
    populateSupervisorProducts();
    if (supervisorTable) {
      await supervisorTable.reload();
    }
  };

  initialize();
});
