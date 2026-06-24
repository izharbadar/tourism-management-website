document.addEventListener("DOMContentLoaded", function () {
  const repeaterSettings = {
    itinerary: {
      containerId: "itineraryRows",
      templateId: "itineraryTemplate",
      rowSelector: ".repeater-item",
    },

    faq: {
      containerId: "faqRows",
      templateId: "faqTemplate",
      rowSelector: ".repeater-item",
    },
  };

  // =========================================
  // ITINERARY HELPERS
  // =========================================

  function getItineraryRows() {
    const container = document.getElementById(
      "itineraryRows"
    );

    if (!container) {
      return [];
    }

    return Array.from(
      container.querySelectorAll(
        ":scope > .repeater-item"
      )
    );
  }

  function updateDayHeading(row) {
    if (!row) {
      return;
    }

    const dayInput = row.querySelector(
      'input[name="itinerary_day_number[]"]'
    );

    const heading = row.querySelector(
      "[data-day-heading]"
    );

    if (!dayInput || !heading) {
      return;
    }

    const dayValue = dayInput.value.trim();

    heading.textContent = dayValue === ""
      ? "Itinerary Day"
      : "Day " + dayValue;
  }

  function getNextDayNumber() {
    const rows = getItineraryRows();

    let highestDay = -1;

    rows.forEach(function (row) {
      const input = row.querySelector(
        'input[name="itinerary_day_number[]"]'
      );

      if (!input) {
        return;
      }

      const value = Number.parseInt(
        input.value,
        10
      );

      if (
        Number.isInteger(value) &&
        value >= 0 &&
        value > highestDay
      ) {
        highestDay = value;
      }
    });

    return highestDay >= 0
      ? highestDay + 1
      : 0;
  }

  function initializeDayHeadings() {
    getItineraryRows().forEach(function (row) {
      updateDayHeading(row);
    });
  }

  // =========================================
  // ADD REPEATER ROW
  // =========================================

  function addRepeaterRow(repeaterType) {
    const settings =
      repeaterSettings[repeaterType];

    if (!settings) {
      return;
    }

    const container = document.getElementById(
      settings.containerId
    );

    const template = document.getElementById(
      settings.templateId
    );

    if (!container || !template) {
      console.error(
        "Repeater container or template missing:",
        repeaterType
      );

      return;
    }

    let nextDayNumber = null;

    if (repeaterType === "itinerary") {
      nextDayNumber = getNextDayNumber();
    }

    const newRow =
      template.content.cloneNode(true);

    container.appendChild(newRow);

    const addedRow =
      container.lastElementChild;

    if (!addedRow) {
      return;
    }

    if (repeaterType === "itinerary") {
      const dayInput = addedRow.querySelector(
        'input[name="itinerary_day_number[]"]'
      );

      if (dayInput) {
        dayInput.value = nextDayNumber;
      }

      updateDayHeading(addedRow);

      const titleInput = addedRow.querySelector(
        'input[name="itinerary_title[]"]'
      );

      if (titleInput) {
        titleInput.focus();
      }
    }

    if (repeaterType === "faq") {
      const questionInput =
        addedRow.querySelector(
          'input[name="faq_question[]"]'
        );

      if (questionInput) {
        questionInput.focus();
      }
    }
  }

  // =========================================
  // CLICK EVENTS
  // =========================================

  document.addEventListener("click", function (event) {
    const addButton = event.target.closest(
      "[data-add-row]"
    );

    if (addButton) {
      event.preventDefault();

      const repeaterType =
        addButton.getAttribute(
          "data-add-row"
        );

      addRepeaterRow(repeaterType);

      return;
    }

    const removeButton = event.target.closest(
      "[data-remove-row]"
    );

    if (!removeButton) {
      return;
    }

    event.preventDefault();

    const row = removeButton.closest(
      ".repeater-item"
    );

    if (!row) {
      return;
    }

    const container = row.parentElement;

    if (!container) {
      return;
    }

    const rows = container.querySelectorAll(
      ":scope > .repeater-item"
    );

    if (rows.length > 1) {
      row.remove();

      return;
    }

    row.querySelectorAll(
      "input, textarea, select"
    ).forEach(function (field) {
      if (field.tagName === "SELECT") {
        field.selectedIndex = 0;
      } else {
        field.value = "";
      }
    });

    if (container.id === "itineraryRows") {
      const dayInput = row.querySelector(
        'input[name="itinerary_day_number[]"]'
      );

      if (dayInput) {
        dayInput.value = 0;
      }

      updateDayHeading(row);
    }
  });

  // Day number manually change ho to heading bhi change ho
  document.addEventListener("input", function (event) {
    if (
      !event.target.matches(
        'input[name="itinerary_day_number[]"]'
      )
    ) {
      return;
    }

    const row = event.target.closest(
      ".repeater-item"
    );

    updateDayHeading(row);
  });

  initializeDayHeadings();

  // =========================================
  // QUILL FULL DESCRIPTION EDITOR
  // =========================================

  const descriptionInput =
    document.getElementById(
      "descriptionInput"
    );

  const descriptionEditor =
    document.getElementById(
      "descriptionEditor"
    );

  if (
    descriptionInput &&
    descriptionEditor &&
    typeof Quill !== "undefined"
  ) {
    const descriptionQuill = new Quill(
      descriptionEditor,
      {
        theme: "snow",

        placeholder:
          "Write complete tour details here...",

        modules: {
          toolbar: [
            [
              {
                header: [
                  2,
                  3,
                  4,
                  false,
                ],
              },
            ],

            [
              "bold",
              "italic",
              "underline",
              "strike",
            ],

            [
              {
                list: "ordered",
              },

              {
                list: "bullet",
              },
            ],

            [
              "blockquote",
              "link",
            ],

            [
              "clean",
            ],
          ],
        },
      }
    );

    const existingDescription =
      descriptionInput.value.trim();

    if (existingDescription) {
      descriptionQuill.clipboard
        .dangerouslyPasteHTML(
          existingDescription
        );
    }

    const tourForm =
      descriptionInput.closest("form");

    if (tourForm) {
      tourForm.addEventListener(
        "submit",
        function (event) {
          const plainText =
            descriptionQuill
              .getText()
              .trim();

          if (!plainText) {
            event.preventDefault();

            window.alert(
              "Please enter the full tour description."
            );

            descriptionQuill.focus();

            return;
          }

          descriptionInput.value =
            descriptionQuill.root.innerHTML;
        }
      );
    }
  }
});