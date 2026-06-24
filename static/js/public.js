document.addEventListener("DOMContentLoaded", function () {
  const menuButton = document.getElementById(
    "publicMenuButton"
  );

  const publicNav = document.getElementById(
    "publicNav"
  );

  if (menuButton && publicNav) {
    menuButton.addEventListener("click", function () {
      publicNav.classList.toggle("active");

      menuButton.textContent =
        publicNav.classList.contains("active")
          ? "×"
          : "☰";
    });

    publicNav.querySelectorAll("a").forEach(function (link) {
      link.addEventListener("click", function () {
        publicNav.classList.remove("active");
        menuButton.textContent = "☰";
      });
    });
  }

  const profileMenus = document.querySelectorAll(
    "[data-profile-menu]"
  );

  profileMenus.forEach(function (profileMenu) {
    const trigger = profileMenu.querySelector(
      "[data-profile-trigger]"
    );

    if (!trigger) {
      return;
    }

    trigger.addEventListener("click", function (event) {
      event.preventDefault();
      event.stopPropagation();

      const isOpen =
        profileMenu.classList.contains("is-open");

      profileMenus.forEach(function (menu) {
        menu.classList.remove("is-open");

        const menuTrigger = menu.querySelector(
          "[data-profile-trigger]"
        );

        if (menuTrigger) {
          menuTrigger.setAttribute(
            "aria-expanded",
            "false"
          );
        }
      });

      if (!isOpen) {
        profileMenu.classList.add("is-open");

        trigger.setAttribute(
          "aria-expanded",
          "true"
        );
      }
    });
  });

  document.addEventListener("click", function (event) {
    profileMenus.forEach(function (profileMenu) {
      if (!profileMenu.contains(event.target)) {
        profileMenu.classList.remove("is-open");

        const trigger = profileMenu.querySelector(
          "[data-profile-trigger]"
        );

        if (trigger) {
          trigger.setAttribute(
            "aria-expanded",
            "false"
          );
        }
      }
    });
  });

  document.addEventListener("keydown", function (event) {
    if (event.key !== "Escape") {
      return;
    }

    if (publicNav) {
      publicNav.classList.remove("active");
    }

    if (menuButton) {
      menuButton.textContent = "☰";
    }

    profileMenus.forEach(function (profileMenu) {
      profileMenu.classList.remove("is-open");
    });
  });
});
