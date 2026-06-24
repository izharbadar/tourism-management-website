document.addEventListener("DOMContentLoaded", function () {
  const input = document.getElementById(
    "galleryImages"
  );

  const fileList = document.getElementById(
    "selectedGalleryFiles"
  );

  const dropZone = document.getElementById(
    "galleryDropZone"
  );

  function displaySelectedFiles() {
    if (!input || !fileList) {
      return;
    }

    fileList.innerHTML = "";

    Array.from(input.files).forEach(
      function (file) {
        const item = document.createElement(
          "span"
        );

        item.textContent = file.name;

        fileList.appendChild(item);
      }
    );
  }

  if (input) {
    input.addEventListener(
      "change",
      displaySelectedFiles
    );
  }

  if (dropZone) {
    [
      "dragenter",
      "dragover",
    ].forEach(function (eventName) {
      dropZone.addEventListener(
        eventName,
        function (event) {
          event.preventDefault();

          dropZone.classList.add(
            "is-dragging"
          );
        }
      );
    });

    [
      "dragleave",
      "drop",
    ].forEach(function (eventName) {
      dropZone.addEventListener(
        eventName,
        function (event) {
          event.preventDefault();

          dropZone.classList.remove(
            "is-dragging"
          );
        }
      );
    });
  }
});
