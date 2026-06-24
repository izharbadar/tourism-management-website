document.addEventListener("DOMContentLoaded", function () {
  const gallery = document.querySelector(
    "[data-public-gallery]"
  );

  if (!gallery) {
    return;
  }

  const items = Array.from(
    gallery.querySelectorAll(
      ".gallery-item"
    )
  );

  const lightbox = document.querySelector(
    "[data-gallery-lightbox]"
  );

  const lightboxImage = lightbox.querySelector(
    "[data-gallery-lightbox-image]"
  );

  const lightboxCounter = lightbox.querySelector(
    "[data-gallery-lightbox-counter]"
  );

  let activeIndex = 0;

  function itemData(item) {
    return {
      src: item.querySelector(
        "[data-lightbox-src]"
      ).textContent.trim(),

      alt: item.querySelector(
        "[data-lightbox-alt]"
      ).textContent.trim(),
    };
  }

  function showItem(index) {
    if (!items.length) {
      return;
    }

    activeIndex = (
      index + items.length
    ) % items.length;

    const data = itemData(
      items[activeIndex]
    );

    lightboxImage.src = data.src;
    lightboxImage.alt = data.alt;

    lightboxCounter.textContent = (
      activeIndex + 1
      + " / "
      + items.length
    );
  }

  function openLightbox(item) {
    const index = items.indexOf(item);

    showItem(
      index >= 0
        ? index
        : 0
    );

    lightbox.hidden = false;

    lightbox.setAttribute(
      "aria-hidden",
      "false"
    );

    document.body.classList.add(
      "gallery-lightbox-open"
    );
  }

  function closeLightbox() {
    lightbox.hidden = true;

    lightbox.setAttribute(
      "aria-hidden",
      "true"
    );

    lightboxImage.src = "";

    document.body.classList.remove(
      "gallery-lightbox-open"
    );
  }

  items.forEach(function (item) {
    const button = item.querySelector(
      "[data-gallery-open]"
    );

    button.addEventListener(
      "click",
      function () {
        openLightbox(item);
      }
    );
  });

  lightbox.querySelector(
    "[data-gallery-close]"
  ).addEventListener(
    "click",
    closeLightbox
  );

  lightbox.querySelector(
    "[data-gallery-previous]"
  ).addEventListener(
    "click",
    function () {
      showItem(activeIndex - 1);
    }
  );

  lightbox.querySelector(
    "[data-gallery-next]"
  ).addEventListener(
    "click",
    function () {
      showItem(activeIndex + 1);
    }
  );

  lightbox.addEventListener(
    "click",
    function (event) {
      if (event.target === lightbox) {
        closeLightbox();
      }
    }
  );

  document.addEventListener(
    "keydown",
    function (event) {
      if (lightbox.hidden) {
        return;
      }

      if (event.key === "Escape") {
        closeLightbox();
      }

      if (event.key === "ArrowLeft") {
        showItem(activeIndex - 1);
      }

      if (event.key === "ArrowRight") {
        showItem(activeIndex + 1);
      }
    }
  );
});
