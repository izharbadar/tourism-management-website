document.addEventListener("DOMContentLoaded", function () {
  const bookingTabs = document.querySelectorAll(
    "[data-booking-tab]"
  );

  const bookingPanels = document.querySelectorAll(
    "[data-booking-panel]"
  );

  function openBookingTab(tabName) {
    bookingTabs.forEach(function (tab) {
      const active =
        tab.dataset.bookingTab === tabName;

      tab.classList.toggle("active", active);
      tab.setAttribute(
        "aria-selected",
        active ? "true" : "false"
      );
    });

    bookingPanels.forEach(function (panel) {
      const active =
        panel.dataset.bookingPanel === tabName;

      panel.classList.toggle("active", active);
      panel.hidden = !active;
    });
  }

  bookingTabs.forEach(function (tab) {
    tab.addEventListener("click", function () {
      openBookingTab(tab.dataset.bookingTab);
    });
  });

  const whatsappNumber = "923271125667";

  document
    .querySelectorAll("[data-whatsapp-link]")
    .forEach(function (link) {
      const message =
        link.dataset.message ||
        "Hello Capture Pakistan.";

      link.href =
        "https://wa.me/" +
        whatsappNumber +
        "?text=" +
        encodeURIComponent(
          message +
          "\n\nTour page: " +
          window.location.href
        );

      link.target = "_blank";
      link.rel = "noopener noreferrer";
    });

  const contactEmail =
    "info@capturepakistan.com";

  document
    .querySelectorAll("[data-email-link]")
    .forEach(function (link) {
      const subject =
        link.dataset.subject ||
        "Tour Quotation";

      const body =
        link.dataset.body ||
        "Hello Capture Pakistan.";

      link.href =
        "mailto:" +
        contactEmail +
        "?subject=" +
        encodeURIComponent(subject) +
        "&body=" +
        encodeURIComponent(
          body +
          "\n\nTour page: " +
          window.location.href
        );
    });

  document
    .querySelectorAll(".accordion-trigger")
    .forEach(function (trigger) {
      trigger.addEventListener("click", function () {
        const content =
          trigger.nextElementSibling;

        if (!content) {
          return;
        }

        const isOpen =
          trigger.getAttribute(
            "aria-expanded"
          ) === "true";

        trigger.setAttribute(
          "aria-expanded",
          isOpen ? "false" : "true"
        );

        content.hidden = isOpen;
      });
    });

  const pricingType =
    document.getElementById("pricingType");

  const quantity =
    document.getElementById("bookingQuantity");

  const quantityLabel =
    document.getElementById("quantityLabel");

  const childCount =
    document.getElementById("childCount");

  const estimatedTotal =
    document.getElementById("estimatedTotal");

  function formatCurrency(value) {
    return new Intl.NumberFormat(
      "en-PK",
      {
        maximumFractionDigits: 0,
      }
    ).format(value);
  }

  function updateBookingTotal() {
    if (
      !pricingType ||
      !quantity ||
      !childCount ||
      !estimatedTotal
    ) {
      return;
    }

    const selectedOption =
      pricingType.options[
        pricingType.selectedIndex
      ];

    const unitPrice = Number(
      selectedOption.dataset.price || 0
    );

    const quantityValue = Number(
      quantity.value || 1
    );

    const childrenValue = Number(
      childCount.value || 0
    );

    const childPrice = Number(
      childCount.dataset.childPrice || 0
    );

    const total =
      unitPrice * quantityValue
      + childPrice * childrenValue;

    estimatedTotal.textContent =
      "PKR " + formatCurrency(total);

    if (quantityLabel) {
      quantityLabel.textContent =
        pricingType.value === "couple"
          ? "Number of Couples"
          : "Adults";
    }
  }

  if (pricingType) {
    pricingType.addEventListener(
      "change",
      updateBookingTotal
    );
  }

  if (quantity) {
    quantity.addEventListener(
      "change",
      updateBookingTotal
    );
  }

  if (childCount) {
    childCount.addEventListener(
      "change",
      updateBookingTotal
    );
  }

  updateBookingTotal();

  const today = new Date();

  const offset =
    today.getTimezoneOffset() * 60000;

  const minimumDate = new Date(
    today.getTime() - offset
  ).toISOString().split("T")[0];

  const travelDate =
    document.getElementById("travelDate");

  if (travelDate) {
    travelDate.min = minimumDate;
  }

  document
    .querySelectorAll("[data-future-date]")
    .forEach(function (dateInput) {
      dateInput.min = minimumDate;
    });

  const shareButton =
    document.getElementById("shareTourButton");

  if (shareButton) {
    shareButton.addEventListener(
      "click",
      async function () {
        try {
          if (navigator.share) {
            await navigator.share({
              title: document.title,
              url: window.location.href,
            });

            return;
          }

          await navigator.clipboard.writeText(
            window.location.href
          );

          shareButton.textContent =
            "✓ Link copied";
        } catch (error) {
          console.error(
            "Sharing failed:",
            error
          );
        }
      }
    );
  }
});
