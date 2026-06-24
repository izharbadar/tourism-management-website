document.addEventListener("DOMContentLoaded", function () {
  const input = document.querySelector(
    "[data-gallery-file-input]"
  );

  const dropZone = document.querySelector(
    "[data-gallery-drop-zone]"
  );

  const count = document.querySelector(
    "[data-gallery-file-count]"
  );

  if (!input || !dropZone || !count) {
    return;
  }

  function updateCount() {
    const total = input.files.length;

    count.textContent = total
      ? total + (total === 1 ? " file selected" : " files selected")
      : "No files selected";

    dropZone.classList.toggle(
      "has-files",
      total > 0
    );
  }

  input.addEventListener(
    "change",
    updateCount
  );

  ["dragenter", "dragover"].forEach(function (eventName) {
    dropZone.addEventListener(
      eventName,
      function () {
        dropZone.classList.add(
          "is-dragging"
        );
      }
    );
  });

  ["dragleave", "drop"].forEach(function (eventName) {
    dropZone.addEventListener(
      eventName,
      function () {
        dropZone.classList.remove(
          "is-dragging"
        );
      }
    );
  });
});
