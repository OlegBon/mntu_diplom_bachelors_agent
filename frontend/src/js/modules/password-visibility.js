function createEyeIcon(isVisible) {
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
  if (isVisible) {
    const slash = document.createElementNS(namespace, "path");
    slash.setAttribute("d", "M4 4 20 20");
    icon.append(slash);
  }
  return icon;
}

function setPasswordVisibility(input, toggle, isVisible) {
  input.type = isVisible ? "text" : "password";
  toggle.replaceChildren(createEyeIcon(isVisible));
  toggle.classList.toggle("is-visible", isVisible);
  toggle.setAttribute("aria-label", isVisible ? "Сховати пароль" : "Показати пароль");
  toggle.setAttribute("aria-pressed", String(isVisible));
  toggle.title = isVisible ? "Сховати пароль" : "Показати пароль";
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
    setPasswordVisibility(input, toggle, false);
    toggle.addEventListener("click", () => setPasswordVisibility(input, toggle, input.type !== "text"));
    wrapper.append(toggle);
  }
}
