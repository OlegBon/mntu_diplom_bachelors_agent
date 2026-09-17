function createEyeIcon() {
  const namespace = "http://www.w3.org/2000/svg";
  const icon = document.createElementNS(namespace, "svg");
  icon.setAttribute("viewBox", "0 0 24 24");
  icon.setAttribute("aria-hidden", "true");
  const outline = document.createElementNS(namespace, "path");
  outline.setAttribute("d", "M2.5 12s3.5-6 9.5-6 9.5 6 9.5 6-3.5 6-9.5 6-9.5-6-9.5-6Z");
  const pupil = document.createElementNS(namespace, "circle");
  pupil.setAttribute("cx", "12");
  pupil.setAttribute("cy", "12");
  pupil.setAttribute("r", "2.5");
  icon.append(outline, pupil);
  return icon;
}

export function initPasswordVisibility(root = document) {
  for (const input of root.querySelectorAll("input[type='password']:not([data-password-visibility-ready])")) {
    input.dataset.passwordVisibilityReady = "true";
    const wrapper = document.createElement("span");
    wrapper.className = "password-control";
    input.parentNode.insertBefore(wrapper, input);
    wrapper.append(input);

    const toggle = document.createElement("button");
    toggle.type = "button";
    toggle.className = "password-control__toggle";
    toggle.setAttribute("aria-label", "Показати пароль");
    toggle.setAttribute("aria-pressed", "false");
    toggle.title = "Показати пароль";
    toggle.append(createEyeIcon());
    toggle.addEventListener("click", () => {
      const visible = input.type === "text";
      input.type = visible ? "password" : "text";
      toggle.setAttribute("aria-label", visible ? "Показати пароль" : "Сховати пароль");
      toggle.setAttribute("aria-pressed", String(!visible));
      toggle.title = visible ? "Показати пароль" : "Сховати пароль";
    });
    wrapper.append(toggle);
  }
}
