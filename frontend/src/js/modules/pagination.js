export function renderPagination(container, { page, totalPages, onPageChange }) {
  container.replaceChildren();
  if (totalPages <= 1) { container.hidden = true; return; }
  container.hidden = false;
  const addButton = (label, targetPage, disabled = false, current = false) => {
    const button = document.createElement("button");
    button.type = "button"; button.className = "page-btn"; button.textContent = label;
    button.disabled = disabled; button.classList.toggle("active", current);
    button.addEventListener("click", () => onPageChange(targetPage)); container.append(button);
  };
  addButton("‹", page - 1, page === 1);
  const pages = [...new Set([1, page - 1, page, page + 1, totalPages].filter((value) => value >= 1 && value <= totalPages))];
  let previous = 0;
  for (const targetPage of pages) {
    if (targetPage - previous > 1) { const gap = document.createElement("span"); gap.textContent = "…"; container.append(gap); }
    addButton(String(targetPage), targetPage, false, targetPage === page); previous = targetPage;
  }
  addButton("›", page + 1, page === totalPages);
}
