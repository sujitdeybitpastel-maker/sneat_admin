document.addEventListener("DOMContentLoaded", async () => {
  const profileForm = document.getElementById("profile-form");
  const passwordForm = document.getElementById("password-form");
  window.appUtils.attachValidationCleanup(profileForm);
  window.appUtils.attachValidationCleanup(passwordForm);
  const profileMeta = document.getElementById("profile-meta");
  const profileValidationRules = {
    "profile-full-name": [
      window.appUtils.validators.required("Full name"),
      window.appUtils.validators.minLength("Full name", 3)
    ],
    "profile-username": [
      window.appUtils.validators.required("Username"),
      window.appUtils.validators.username()
    ],
    "profile-email": [
      window.appUtils.validators.required("Email"),
      window.appUtils.validators.email()
    ]
  };
  const passwordValidationRules = {
    "current-password": [window.appUtils.validators.required("Current password")],
    "new-password": [
      window.appUtils.validators.required("New password"),
      window.appUtils.validators.minLength("New password", 8),
      (value, _field, form) => {
        const currentPassword = form.querySelector("#current-password")?.value || "";
        return currentPassword && currentPassword === value
          ? "New password must be different from the current password."
          : "";
      }
    ],
    "confirm-password": [
      window.appUtils.validators.required("Confirm new password"),
      window.appUtils.validators.passwordMatch("new-password", "Confirm new password")
    ]
  };

  const setProfileMeta = (profile) => {
    profileMeta.textContent = `Role: ${profile.role_label} - Last updated ${profile.updated_at}`;
  };

  const loadProfile = async () => {
    const profile = await window.appUtils.json("/users/api/profile");
    document.getElementById("profile-full-name").value = profile.full_name;
    document.getElementById("profile-username").value = profile.username;
    document.getElementById("profile-email").value = profile.email;
    setProfileMeta(profile);
  };

  profileForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    if (!window.appUtils.validateForm(profileForm, profileValidationRules)) {
      return;
    }
    const payload = {
      full_name: document.getElementById("profile-full-name").value,
      username: document.getElementById("profile-username").value,
      email: document.getElementById("profile-email").value
    };

    try {
      const profile = await window.appUtils.json("/users/api/profile", {
        method: "PATCH",
        body: JSON.stringify(payload)
      });
      setProfileMeta(profile);
      alert("Profile updated successfully.");
    } catch (error) {
      if (error.fieldErrors && Object.keys(error.fieldErrors).length) {
        window.appUtils.applyBackendErrors(profileForm, error.fieldErrors);
        return;
      }
      alert(error.message);
    }
  });

  passwordForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    if (!window.appUtils.validateForm(passwordForm, passwordValidationRules)) {
      return;
    }
    const payload = {
      current_password: document.getElementById("current-password").value,
      new_password: document.getElementById("new-password").value,
      confirm_password: document.getElementById("confirm-password").value
    };

    try {
      await window.appUtils.json("/users/api/profile/password", {
        method: "PATCH",
        body: JSON.stringify(payload)
      });
      passwordForm.reset();
      alert("Password changed successfully.");
    } catch (error) {
      if (error.fieldErrors && Object.keys(error.fieldErrors).length) {
        window.appUtils.applyBackendErrors(passwordForm, error.fieldErrors);
        return;
      }
      alert(error.message);
    }
  });

  await loadProfile();
});
