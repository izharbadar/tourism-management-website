document.addEventListener("DOMContentLoaded", function () {
  const sidebar = document.getElementById("adminSidebar");
  const menuButton = document.getElementById("adminMenuButton");
  const overlay = document.getElementById("sidebarOverlay");

  function closeSidebar() {
    if (sidebar) {
      sidebar.classList.remove("mobile-open");
    }

    if (overlay) {
      overlay.classList.remove("active");
    }
  }

  if (menuButton && sidebar && overlay) {
    menuButton.addEventListener("click", function () {
      sidebar.classList.toggle("mobile-open");
      overlay.classList.toggle("active");
    });
  }

  if (overlay) {
    overlay.addEventListener("click", closeSidebar);
  }

  document.querySelectorAll("[data-confirm]").forEach(function (form) {
    form.addEventListener("submit", function (event) {
      const message = form.getAttribute("data-confirm");

      if (!window.confirm(message)) {
        event.preventDefault();
      }
    });
  });
});