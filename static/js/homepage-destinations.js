document.addEventListener("DOMContentLoaded", function () {
  const track = document.getElementById("destinationsTrack");
  if (!track) return;

  const controls = Array.from(
    document.querySelectorAll('[data-scroll="destinationsTrack"]')
  );
  const cards = Array.from(track.querySelectorAll(".destination-card"));
  const autoplayDelay = 4500;
  let autoplayTimer = null;
  let interactionTimer = null;
  let interacting = false;

  function cardStep() {
    const firstCard = cards[0];
    if (!firstCard) return track.clientWidth;
    const styles = window.getComputedStyle(track);
    const gap = parseFloat(styles.columnGap || styles.gap || "0");
    return firstCard.getBoundingClientRect().width + gap;
  }

  function maximumScroll() {
    return Math.max(0, track.scrollWidth - track.clientWidth);
  }

  function updateButtons() {
    const maximum = maximumScroll();
    controls.forEach(function (control) {
      const direction = Number(control.getAttribute("data-direction"));
      const atStart = track.scrollLeft <= 3;
      const atEnd = track.scrollLeft >= maximum - 3;
      control.disabled = direction < 0 ? atStart : atEnd;
    });
  }

  function move(direction) {
    const maximum = maximumScroll();
    if (maximum <= 1) return;

    if (direction > 0 && track.scrollLeft >= maximum - 5) {
      track.scrollTo({ left: 0, behavior: "smooth" });
      return;
    }

    if (direction < 0 && track.scrollLeft <= 5) {
      track.scrollTo({ left: maximum, behavior: "smooth" });
      return;
    }

    track.scrollBy({
      left: cardStep() * direction,
      behavior: "smooth",
    });
  }

  function stopAutoplay() {
    if (autoplayTimer) {
      window.clearInterval(autoplayTimer);
      autoplayTimer = null;
    }
  }

  function startAutoplay() {
    stopAutoplay();
    if (interacting || cards.length <= 1 || maximumScroll() <= 1) return;
    autoplayTimer = window.setInterval(function () {
      move(1);
    }, autoplayDelay);
  }

  function pauseForInteraction() {
    interacting = true;
    stopAutoplay();
    if (interactionTimer) window.clearTimeout(interactionTimer);
    interactionTimer = window.setTimeout(function () {
      interacting = false;
      startAutoplay();
    }, 6000);
  }

  controls.forEach(function (button) {
    button.addEventListener("click", function () {
      move(Number(button.getAttribute("data-direction")));
      pauseForInteraction();
    });
  });

  track.addEventListener("scroll", updateButtons, { passive: true });
  track.addEventListener("touchstart", pauseForInteraction, { passive: true });
  track.addEventListener("pointerdown", pauseForInteraction);
  track.addEventListener("mouseenter", function () {
    interacting = true;
    stopAutoplay();
  });
  track.addEventListener("mouseleave", function () {
    interacting = false;
    startAutoplay();
  });

  document.addEventListener("visibilitychange", function () {
    if (document.hidden) stopAutoplay();
    else startAutoplay();
  });

  window.addEventListener("resize", function () {
    updateButtons();
    startAutoplay();
  });

  updateButtons();
  startAutoplay();
});
