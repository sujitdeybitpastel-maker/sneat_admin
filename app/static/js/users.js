document.addEventListener("DOMContentLoaded", () => {
  const modalElement = document.getElementById("userModal");
  const modal = new bootstrap.Modal(modalElement);
  const form = document.getElementById("user-form");
  const selectedUserIds = new Set();
  const selectAllCheckbox = document.getElementById("users-select-all");
  window.appUtils.attachValidationCleanup(form);
  const fields = ["full_name", "username", "email", "role", "status", "password"];
  const validationRules = {
    full_name: [
      window.appUtils.validators.required("Full name"),
      window.appUtils.validators.minLength("Full name", 3)
    ],
    username: [
      window.appUtils.validators.required("Username"),
      window.appUtils.validators.username()
    ],
    email: [
      window.appUtils.validators.required("Email"),
      window.appUtils.validators.email()
    ],
    role: [window.appUtils.validators.required("Role")],
    status: [window.appUtils.validators.required("Status")],
    password: [
      (value) => {
        const isEditing = Boolean(document.getElementById("user-id").value);
        if (!isEditing && !value) return "Password is required for a new user.";
        if (value && value.length < 8) return "Password must be at least 8 characters.";
        return "";
      }
    ]
  };

  const table = new SimpleDataTable({
    tableBodySelector: "#users-table tbody",
    paginationSelector: "#users-pagination",
    searchSelector: "#users-search",
    emptyColumns: 8,
    fetchData: async () => window.appUtils.json("/users/api"),
    renderRow: (row) => `
      <tr>
        <td class="text-center"><input class="form-check-input user-row-checkbox" type="checkbox" data-id="${row.id}" ${selectedUserIds.has(String(row.id)) ? "checked" : ""} aria-label="Select user ${row.full_name}" /></td>
        <td><strong>${row.full_name}</strong></td>
        <td>${row.username}</td>
        <td>${row.email}</td>
        <td><span class="text-uppercase">${row.role_label}</span></td>
        <td>${window.appUtils.badge(row.status_label)}</td>
        <td>${row.created_at}</td>
        <td>
          <button class="btn btn-sm btn-outline-primary me-1" data-action="edit" data-id="${row.id}">${window.appUtils.icon("edit", "me-1")}Edit</button>
          <button class="btn btn-sm btn-outline-secondary" data-action="toggle" data-id="${row.id}">${window.appUtils.icon("toggle", "me-1")}${row.status === "1" ? "Inactivate" : "Activate"}</button>
        </td>
      </tr>`,
    afterRender: (_pageRows, filteredRows) => {
      const ids = filteredRows.map((row) => String(row.id));
      const allSelected = ids.length > 0 && ids.every((id) => selectedUserIds.has(id));
      const someSelected = ids.some((id) => selectedUserIds.has(id));
      if (selectAllCheckbox) {
        selectAllCheckbox.checked = allSelected;
        selectAllCheckbox.indeterminate = !allSelected && someSelected;
      }
    }
  });

  const resetForm = () => {
    form.reset();
    window.appUtils.clearFormErrors(form);
    document.getElementById("user-id").value = "";
    document.getElementById("user-modal-title").textContent = "Add User";
  };

  document.getElementById("add-user-btn").addEventListener("click", resetForm);
  document.getElementById("download-users-btn")?.addEventListener("click", () => {
    const ids = Array.from(selectedUserIds);
    const query = ids.length ? `?ids=${ids.join(",")}` : "";
    window.location.href = `/users/api/export${query}`;
  });

  selectAllCheckbox?.addEventListener("change", () => {
    const visibleIds = table.filteredRows.map((row) => String(row.id));
    if (selectAllCheckbox.checked) {
      visibleIds.forEach((id) => selectedUserIds.add(id));
    } else {
      visibleIds.forEach((id) => selectedUserIds.delete(id));
    }
    table.render();
  });

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    if (!window.appUtils.validateForm(form, validationRules)) {
      return;
    }
    const id = document.getElementById("user-id").value;
    const payload = Object.fromEntries(fields.map((field) => [field, document.getElementById(field).value]));
    try {
      await window.appUtils.json(id ? `/users/api/${id}` : "/users/api", {
        method: id ? "PUT" : "POST",
        body: JSON.stringify(payload)
      });
      modal.hide();
      resetForm();
      await table.reload();
    } catch (error) {
      if (error.fieldErrors && Object.keys(error.fieldErrors).length) {
        window.appUtils.applyBackendErrors(form, error.fieldErrors);
        return;
      }
      alert(error.message);
    }
  });

  document.querySelector("#users-table tbody").addEventListener("click", async (event) => {
    const checkbox = event.target.closest(".user-row-checkbox");
    if (checkbox) {
      const id = String(checkbox.dataset.id);
      if (checkbox.checked) {
        selectedUserIds.add(id);
      } else {
        selectedUserIds.delete(id);
      }
      table.render();
      return;
    }

    const button = event.target.closest("button[data-action]");
    if (!button) return;

    const id = button.dataset.id;
    const row = table.rows.find((item) => String(item.id) === id);

    if (button.dataset.action === "edit" && row) {
      document.getElementById("user-id").value = row.id;
      document.getElementById("user-modal-title").textContent = "Edit User";
      document.getElementById("full_name").value = row.full_name;
      document.getElementById("username").value = row.username;
      document.getElementById("email").value = row.email;
      document.getElementById("role").value = row.role;
      document.getElementById("status").value = row.status;
      document.getElementById("password").value = "";
      modal.show();
    }

    if (button.dataset.action === "toggle") {
      try {
        await window.appUtils.json(`/users/api/${id}/status`, { method: "PATCH" });
        await table.reload();
      } catch (error) {
        alert(error.message);
      }
    }
  });

  table.reload().then(() => window.appUtils.enhanceDynamicUI());
});
