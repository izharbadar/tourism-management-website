document.addEventListener("DOMContentLoaded", function () {
  document
    .querySelectorAll("[data-accordion-trigger]")
    .forEach(function (button) {
      button.addEventListener("click", function () {
        const item = button.closest("article");

        if (!item) {
          return;
        }

        const accordion = item.closest("[data-accordion]");

        if (accordion) {
          accordion
            .querySelectorAll("article")
            .forEach(function (otherItem) {
              if (otherItem !== item) {
                otherItem.classList.remove("is-open");
              }
            });
        }

        item.classList.toggle("is-open");
      });
    });
});
