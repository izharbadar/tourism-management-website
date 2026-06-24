document.addEventListener("DOMContentLoaded", function () {
  const sidebar = document.getElementById("adminSidebar");

  const menuButton = document.getElementById(
    "adminMenuButton"
  );

  const overlay = document.getElementById(
    "adminSidebarOverlay"
  );

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

  document.addEventListener("keydown", function (event) {
    if (event.key === "Escape") {
      closeSidebar();
    }
  });

  document
    .querySelectorAll(".admin-sidebar .sidebar-link")
    .forEach(function (link) {
      link.addEventListener("click", function () {
        if (window.innerWidth <= 970) {
          closeSidebar();
        }
      });
    });
});