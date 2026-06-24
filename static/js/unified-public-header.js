document.addEventListener("DOMContentLoaded", function () {
  const header = document.getElementById(
    "siteHeader"
  );

  const menuButton = document.getElementById(
    "mobileMenuBtn"
  );

  const navigation = document.getElementById(
    "mainNavigation"
  );

  if (
    header
    && menuButton
    && navigation
  ) {
    menuButton.addEventListener(
      "click",
      function (event) {
        event.preventDefault();
        event.stopPropagation();

        const menuIsOpen =
          header.classList.toggle(
            "menu-open"
          );

        menuButton.setAttribute(
          "aria-expanded",
          menuIsOpen
            ? "true"
            : "false"
        );
      }
    );

    navigation
      .querySelectorAll("a")
      .forEach(function (link) {
        link.addEventListener(
          "click",
          function () {
            header.classList.remove(
              "menu-open"
            );

            menuButton.setAttribute(
              "aria-expanded",
              "false"
            );
          }
        );
      });

    document.addEventListener(
      "click",
      function (event) {
        if (
          !header.contains(
            event.target
          )
        ) {
          header.classList.remove(
            "menu-open"
          );

          menuButton.setAttribute(
            "aria-expanded",
            "false"
          );
        }
      }
    );

    document.addEventListener(
      "keydown",
      function (event) {
        if (event.key === "Escape") {
          header.classList.remove(
            "menu-open"
          );

          menuButton.setAttribute(
            "aria-expanded",
            "false"
          );
        }
      }
    );
  }
});
