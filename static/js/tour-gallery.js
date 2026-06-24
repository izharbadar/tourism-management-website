document.addEventListener("DOMContentLoaded", function () {
  const sourceElements =
    document.querySelectorAll(
      "[data-gallery-source]"
    );

  const galleryItems = Array.from(
    sourceElements
  ).map(function (element) {
    return {
      source:
        element.dataset.gallerySource,
      alt:
        element.dataset.galleryAlt || "",
    };
  });

  const lightbox = document.getElementById(
    "tourGalleryLightbox"
  );

  const lightboxImage =
    document.getElementById(
      "lightboxGalleryImage"
    );

  const caption =
    document.getElementById(
      "lightboxGalleryCaption"
    );

  const counter =
    document.getElementById(
      "lightboxGalleryCounter"
    );

  const previousButton =
    document.querySelector(
      "[data-gallery-previous]"
    );

  const nextButton =
    document.querySelector(
      "[data-gallery-next]"
    );

  let currentIndex = 0;

  function renderImage() {
    if (
      !galleryItems.length ||
      !lightboxImage
    ) {
      return;
    }

    const item =
      galleryItems[currentIndex];

    lightboxImage.src = item.source;
    lightboxImage.alt = item.alt;

    if (caption) {
      caption.textContent = item.alt;
    }

    if (counter) {
      counter.textContent =
        (currentIndex + 1)
        + " / "
        + galleryItems.length;
    }

    if (previousButton) {
      previousButton.disabled =
        galleryItems.length <= 1;
    }

    if (nextButton) {
      nextButton.disabled =
        galleryItems.length <= 1;
    }
  }

  function openGallery(index) {
    if (
      !lightbox ||
      !galleryItems.length
    ) {
      return;
    }

    currentIndex = Math.min(
      Math.max(index, 0),
      galleryItems.length - 1
    );

    renderImage();

    lightbox.hidden = false;
    lightbox.setAttribute(
      "aria-hidden",
      "false"
    );

    document.body.classList.add(
      "gallery-lightbox-open"
    );
  }

  function closeGallery() {
    if (!lightbox) {
      return;
    }

    lightbox.hidden = true;
    lightbox.setAttribute(
      "aria-hidden",
      "true"
    );

    document.body.classList.remove(
      "gallery-lightbox-open"
    );
  }

  function showPrevious() {
    if (!galleryItems.length) {
      return;
    }

    currentIndex =
      (
        currentIndex
        - 1
        + galleryItems.length
      )
      % galleryItems.length;

    renderImage();
  }

  function showNext() {
    if (!galleryItems.length) {
      return;
    }

    currentIndex =
      (
        currentIndex + 1
      )
      % galleryItems.length;

    renderImage();
  }

  document
    .querySelectorAll(
      "[data-gallery-open]"
    )
    .forEach(function (button) {
      button.addEventListener(
        "click",
        function () {
          openGallery(
            Number(
              button.dataset.galleryOpen
              || 0
            )
          );
        }
      );
    });

  document
    .querySelectorAll(
      "[data-gallery-close]"
    )
    .forEach(function (button) {
      button.addEventListener(
        "click",
        closeGallery
      );
    });

  if (previousButton) {
    previousButton.addEventListener(
      "click",
      showPrevious
    );
  }

  if (nextButton) {
    nextButton.addEventListener(
      "click",
      showNext
    );
  }

  if (lightbox) {
    lightbox.addEventListener(
      "click",
      function (event) {
        if (event.target === lightbox) {
          closeGallery();
        }
      }
    );
  }

  document.addEventListener(
    "keydown",
    function (event) {
      if (
        !lightbox
        || lightbox.hidden
      ) {
        return;
      }

      if (event.key === "Escape") {
        closeGallery();
      }

      if (event.key === "ArrowLeft") {
        showPrevious();
      }

      if (event.key === "ArrowRight") {
        showNext();
      }
    }
  );
});
