document.addEventListener("DOMContentLoaded", function () {
  document
    .querySelectorAll("[data-password-toggle]")
    .forEach(function (button) {
      button.addEventListener(
        "click",
        function () {
          const inputId =
            button.getAttribute(
              "data-password-toggle"
            );

          const input =
            document.getElementById(
              inputId
            );

          if (!input) {
            return;
          }

          const isVisible =
            input.type === "text";

          input.type = (
            isVisible
            ? "password"
            : "text"
          );

          button.textContent = (
            isVisible
            ? "Show"
            : "Hide"
          );
        }
      );
    });
});
