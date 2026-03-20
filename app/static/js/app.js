const LOTTIE_LIBRARY = {
  home: "https://assets3.lottiefiles.com/packages/lf20_jtbfg2nb.json",
  box: "https://assets2.lottiefiles.com/packages/lf20_w51pcehl.json",
  user: "https://assets9.lottiefiles.com/packages/lf20_touohxv0.json",
  team: "https://assets10.lottiefiles.com/packages/lf20_kkflmtur.json",
  globe: "https://assets9.lottiefiles.com/packages/lf20_isdnoxqy.json",
  sparkle: "https://assets3.lottiefiles.com/packages/lf20_6AxxXH.json",
  logout: "https://assets1.lottiefiles.com/packages/lf20_xlkxtmul.json",
  plus: "https://assets2.lottiefiles.com/packages/lf20_zrqthn6o.json",
  eye: "https://assets10.lottiefiles.com/packages/lf20_4kx2q32n.json",
  "arrow-left": "https://assets10.lottiefiles.com/private_files/lf30_obidsi0t.json",
  edit: "https://assets4.lottiefiles.com/packages/lf20_wx4nmpm1.json",
  toggle: "https://assets8.lottiefiles.com/packages/lf20_j1adxtyb.json",
  bell: "https://assets2.lottiefiles.com/packages/lf20_bkmfzg3t.json"
};

const LINE_ICON_LIBRARY = {
  home: `
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" aria-hidden="true">
      <path d="M3 10.5 12 3l9 7.5" />
      <path d="M5.5 9.5V20h13V9.5" />
      <path d="M9.5 20v-5h5v5" />
    </svg>`,
  box: `
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" aria-hidden="true">
      <path d="m3 7 9-4 9 4-9 4-9-4Z" />
      <path d="M3 7v10l9 4 9-4V7" />
      <path d="M12 11v10" />
    </svg>`,
  user: `
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" aria-hidden="true">
      <circle cx="12" cy="8" r="3.5" />
      <path d="M5 19c1.5-3 4-4.5 7-4.5s5.5 1.5 7 4.5" />
    </svg>`,
  team: `
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" aria-hidden="true">
      <circle cx="9" cy="8.5" r="2.5" />
      <circle cx="16.5" cy="9.5" r="2" />
      <path d="M4.5 19c1.2-2.6 3.3-4 6-4 2.8 0 4.9 1.4 6.2 4" />
      <path d="M15 15.3c1.7.2 3 1 4.2 2.7" />
    </svg>`,
  globe: `
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" aria-hidden="true">
      <circle cx="12" cy="12" r="8.5" />
      <path d="M3.8 12h16.4" />
      <path d="M12 3.5c2.4 2.2 3.8 5.2 3.8 8.5S14.4 18.3 12 20.5c-2.4-2.2-3.8-5.2-3.8-8.5S9.6 5.7 12 3.5Z" />
    </svg>`,
  sparkle: `
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" aria-hidden="true">
      <path d="m12 3 1.8 5.2L19 10l-5.2 1.8L12 17l-1.8-5.2L5 10l5.2-1.8L12 3Z" />
      <path d="m18.5 3.5.7 2 .8.3-2 .7-.7 2-.7-2-.8-.3 2-.7.7-2Z" />
    </svg>`,
  logout: `
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" aria-hidden="true">
      <path d="M10 5H6.5A2.5 2.5 0 0 0 4 7.5v9A2.5 2.5 0 0 0 6.5 19H10" />
      <path d="M13 8.5 17.5 12 13 15.5" />
      <path d="M9 12h8.5" />
    </svg>`,
  plus: `
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" aria-hidden="true">
      <path d="M12 5v14" />
      <path d="M5 12h14" />
    </svg>`,
  eye: `
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" aria-hidden="true">
      <path d="M2.5 12S6 6.5 12 6.5 21.5 12 21.5 12 18 17.5 12 17.5 2.5 12 2.5 12Z" />
      <circle cx="12" cy="12" r="2.5" />
    </svg>`,
  "arrow-left": `
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" aria-hidden="true">
      <path d="m14.5 5-7 7 7 7" />
      <path d="M8 12h9" />
    </svg>`,
  edit: `
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" aria-hidden="true">
      <path d="m4 20 4.2-1 9.1-9.1a2 2 0 0 0 0-2.8l-.4-.4a2 2 0 0 0-2.8 0L5 15.8 4 20Z" />
      <path d="m12.8 7.2 4 4" />
    </svg>`,
  toggle: `
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" aria-hidden="true">
      <rect x="3.5" y="7.5" width="17" height="9" rx="4.5" />
      <circle cx="9" cy="12" r="3" />
    </svg>`,
  bell: `
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" aria-hidden="true">
      <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9" />
      <path d="M13.73 21a2 2 0 0 1-3.46 0" />
    </svg>`
};

function initLottieIcons(root = document) {
  if (!window.lottie) return;
  root.querySelectorAll(".lottie-icon").forEach((node) => {
    if (node.dataset.iconPrepared !== "true") {
      node.dataset.iconPrepared = "true";
      node.innerHTML = `
        <span class="line-icon-shell">${LINE_ICON_LIBRARY[node.dataset.lottie] || ""}</span>
        <span class="lottie-player-shell" aria-hidden="true"></span>
      `;
    }
    if (node.dataset.lottieMounted === "true") return;
    const animationPath = LOTTIE_LIBRARY[node.dataset.lottie];
    if (!animationPath) return;

    const container = node.querySelector(".lottie-player-shell");
    if (!container) return;

    node.dataset.lottieMounted = "true";
    const animation = window.lottie.loadAnimation({
      container,
      renderer: "svg",
      loop: false,
      autoplay: false,
      path: animationPath
    });

    node._lottieAnimation = animation;
    node.addEventListener("mouseenter", () => {
      animation.stop();
      animation.play();
      node.classList.add("is-animating");
    });
    node.addEventListener("mouseleave", () => {
      node.classList.remove("is-animating");
    });
    node.addEventListener("focusin", () => {
      animation.stop();
      animation.play();
      node.classList.add("is-animating");
    });
    node.addEventListener("focusout", () => {
      node.classList.remove("is-animating");
    });
    animation.addEventListener("complete", () => {
      if (!node.matches(":hover") && !node.matches(":focus-within")) {
        node.classList.remove("is-animating");
      }
    });
  });
}

function escapeHtml(str) {
  if (str == null) return "";
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

window.escapeHtml = escapeHtml;

window.appUtils = {
  currency(value) {
    return new Intl.NumberFormat("en-IN", {
      style: "currency",
      currency: "USD",
      maximumFractionDigits: 2
    }).format(value || 0);
  },
  badge(status) {
    const normalized = String(status).toLowerCase();
    const badgeClass =
      normalized === "active"
        ? "bg-label-primary"
        : normalized === "inactive"
          ? "bg-label-secondary"
          : "bg-label-warning";
    return `<span class="badge ${badgeClass} status-badge">${escapeHtml(status)}</span>`;
  },
  icon(name, extraClass = "") {
    const className = ["lottie-icon", extraClass].filter(Boolean).join(" ");
    return `<span class="${className}" data-lottie="${name}" aria-hidden="true"></span>`;
  },
  formatDate(value) {
    if (!value) return "";
    const d = new Date(value);
    const dd = String(d.getDate()).padStart(2, "0");
    const mm = String(d.getMonth() + 1).padStart(2, "0");
    const yyyy = d.getFullYear();
    return `${dd}-${mm}-${yyyy}`;
  },
  enhanceDynamicUI(root = document) {
    initLottieIcons(root);
  },
  showFieldError(field, message) {
    field.classList.add("is-invalid");
    let feedback = field.parentElement?.querySelector(".invalid-feedback[data-generated='true']");
    if (!feedback) {
      feedback = document.createElement("div");
      feedback.className = "invalid-feedback";
      feedback.dataset.generated = "true";
      field.parentElement?.appendChild(feedback);
    }
    feedback.textContent = message;
  },
  clearFieldError(field) {
    field.classList.remove("is-invalid");
    const feedback = field.parentElement?.querySelector(".invalid-feedback[data-generated='true']");
    if (feedback) feedback.remove();
  },
  clearFormErrors(form) {
    form.querySelectorAll(".is-invalid").forEach((field) => field.classList.remove("is-invalid"));
    form.querySelectorAll(".invalid-feedback[data-generated='true']").forEach((node) => node.remove());
  },
  applyBackendErrors(form, fieldErrors = {}) {
    Object.entries(fieldErrors).forEach(([fieldId, message]) => {
      const field = form.querySelector(`#${fieldId}`);
      if (field && message) {
        window.appUtils.showFieldError(field, message);
      }
    });
  },
  validateForm(form, rules) {
    window.appUtils.clearFormErrors(form);
    let isValid = true;

    Object.entries(rules).forEach(([fieldId, validators]) => {
      const field = form.querySelector(`#${fieldId}`);
      if (!field) return;
      const value =
        typeof field.value === "string" && field.type !== "password"
          ? field.value.trim()
          : field.value;

      for (const validator of validators) {
        const message = validator(value, field, form);
        if (message) {
          isValid = false;
          window.appUtils.showFieldError(field, message);
          break;
        }
      }
    });

    return isValid;
  },
  attachValidationCleanup(form) {
    form.querySelectorAll("input, select, textarea").forEach((field) => {
      if (field.dataset.validationCleanupBound === "true") return;
      field.dataset.validationCleanupBound = "true";
      const clear = () => window.appUtils.clearFieldError(field);
      field.addEventListener("input", clear);
      field.addEventListener("change", clear);
    });
  },
  validators: {
    required: (label) => (value) => (!value ? `${label} is required.` : ""),
    minLength: (label, min) => (value) => (value && value.length < min ? `${label} must be at least ${min} characters.` : ""),
    email: () => (value) => (!value || /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value) ? "" : "Enter a valid email address."),
    positiveNumber: (label) => (value) => (value === "" || Number(value) <= 0 ? `${label} must be greater than 0.` : ""),
    nonNegativeInteger: (label) => (value) =>
      value === "" || !Number.isInteger(Number(value)) || Number(value) < 0 ? `${label} must be a non-negative whole number.` : "",
    username: () => (value) =>
      !value || /^[a-zA-Z0-9._-]{3,}$/.test(value) ? "" : "Username must be at least 3 characters and use only letters, numbers, dot, underscore, or hyphen.",
    passwordMatch: (sourceId, label) => (value, _field, form) => {
      const source = form.querySelector(`#${sourceId}`);
      return source && source.value !== value ? `${label} does not match.` : "";
    }
  },
  async setTheme(themeMode) {
    const response = await window.appUtils.json("/users/theme", {
      method: "POST",
      body: JSON.stringify({ theme_mode: themeMode })
    });
    applyTheme(response.theme_mode);
    return response.theme_mode;
  },
  async json(url, options = {}) {
    const response = await fetch(url, {
      headers: { "Content-Type": "application/json" },
      ...options
    });
    if (!response.ok) {
      let message = "Request failed";
      let fieldErrors = {};
      try {
        const data = await response.json();
        message = data.message || message;
        fieldErrors = data.field_errors || {};
      } catch (error) {
        message = response.statusText || message;
      }
      const apiError = new Error(message);
      apiError.fieldErrors = fieldErrors;
      throw apiError;
    }
    return response.status === 204 ? null : response.json();
  }
};

function applyTheme(themeMode) {
  const root = document.documentElement;
  const systemDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
  const resolvedTheme = themeMode === "system" ? (systemDark ? "dark" : "light") : themeMode;

  root.dataset.appTheme = themeMode;
  root.dataset.resolvedTheme = resolvedTheme;
  root.classList.toggle("dark-style", resolvedTheme === "dark");
  root.classList.toggle("light-style", resolvedTheme !== "dark");

  const label = document.getElementById("theme-toggle-label");
  if (label) {
    label.textContent = `${themeMode.charAt(0).toUpperCase()}${themeMode.slice(1)}`;
  }

  document.querySelectorAll(".theme-option").forEach((button) => {
    button.classList.toggle("active", button.dataset.themeMode === themeMode);
  });

  window.dispatchEvent(new CustomEvent("theme:changed", { detail: { themeMode, resolvedTheme } }));
}

document.addEventListener("DOMContentLoaded", () => {
  applyTheme(document.documentElement.dataset.appTheme || "system");
  initLottieIcons();

  document.querySelectorAll(".theme-option").forEach((button) => {
    button.addEventListener("click", async () => {
      await window.appUtils.setTheme(button.dataset.themeMode);
    });
  });

  const media = window.matchMedia("(prefers-color-scheme: dark)");
  const handleMediaChange = () => {
    if ((document.documentElement.dataset.appTheme || "system") === "system") {
      applyTheme("system");
    }
  };

  if (typeof media.addEventListener === "function") {
    media.addEventListener("change", handleMediaChange);
  } else if (typeof media.addListener === "function") {
    media.addListener(handleMediaChange);
  }
});
