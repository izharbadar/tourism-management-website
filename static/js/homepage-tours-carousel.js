document.addEventListener("DOMContentLoaded", function () {
  const shell = document.querySelector(
    "[data-tour-carousel]"
  );

  const track = document.getElementById(
    "homepageToursTrack"
  );

  if (!shell || !track) {
    return;
  }

  const cards = Array.from(
    track.querySelectorAll(
      ".homepage-tour-card"
    )
  );

  const controls = Array.from(
    document.querySelectorAll(
      '[data-tour-scroll="homepageToursTrack"]'
    )
  );

  const progressBar = shell.querySelector(
    "[data-tour-progress]"
  );

  const autoplayButton = shell.querySelector(
    "[data-tour-autoplay-control]"
  );

  const delay = Math.max(
    2500,
    Number(
      shell.getAttribute(
        "data-autoplay-delay"
      )
    ) || 4500
  );

  let autoplayTimer = null;
  let autoplayPaused = false;
  let userIsInteracting = false;
  let resumeTimer = null;

  function cardStep() {
    const firstCard = cards[0];

    if (!firstCard) {
      return track.clientWidth;
    }

    const styles =
      window.getComputedStyle(track);

    const gap = parseFloat(
      styles.columnGap
      || styles.gap
      || "0"
    );

    return (
      firstCard.getBoundingClientRect().width
      + gap
    );
  }

  function maximumScroll() {
    return Math.max(
      0,
      track.scrollWidth
      - track.clientWidth
    );
  }

  function currentProgress() {
    const maximum = maximumScroll();

    if (maximum <= 1) {
      return 100;
    }

    return Math.min(
      100,
      Math.max(
        0,
        track.scrollLeft
        / maximum
        * 100
      )
    );
  }

  function updateUi() {
    const maximum = maximumScroll();
    const atStart = track.scrollLeft <= 3;
    const atEnd =
      track.scrollLeft
      >= maximum - 3;

    controls.forEach(
      function (control) {
        const direction = Number(
          control.getAttribute(
            "data-direction"
          )
        );

        control.disabled = (
          direction < 0
            ? atStart
            : atEnd
        );

        control.setAttribute(
          "aria-disabled",
          control.disabled
            ? "true"
            : "false"
        );
      }
    );

    if (progressBar) {
      const visibleWidth = Math.min(
        100,
        (
          track.clientWidth
          / Math.max(
            track.scrollWidth,
            1
          )
          * 100
        )
      );

      const progress =
        maximum <= 1
          ? 100
          : Math.max(
              visibleWidth,
              currentProgress()
            );

      progressBar.style.width =
        progress + "%";
    }
  }

  function move(direction) {
    const maximum = maximumScroll();

    if (maximum <= 1) {
      return;
    }

    if (
      direction > 0
      && track.scrollLeft
        >= maximum - 5
    ) {
      track.scrollTo({
        left: 0,
        behavior: "smooth",
      });

      return;
    }

    if (
      direction < 0
      && track.scrollLeft <= 5
    ) {
      track.scrollTo({
        left: maximum,
        behavior: "smooth",
      });

      return;
    }

    track.scrollBy({
      left: (
        cardStep()
        * direction
      ),
      behavior: "smooth",
    });
  }

  function clearAutoplay() {
    if (autoplayTimer) {
      window.clearInterval(
        autoplayTimer
      );

      autoplayTimer = null;
    }
  }

  function startAutoplay() {
    clearAutoplay();

    if (
      autoplayPaused
      || userIsInteracting
      || cards.length <= 1
      || maximumScroll() <= 1
    ) {
      return;
    }

    autoplayTimer =
      window.setInterval(
        function () {
          move(1);
        },
        delay
      );
  }

  function pauseForInteraction() {
    userIsInteracting = true;
    clearAutoplay();

    if (resumeTimer) {
      window.clearTimeout(
        resumeTimer
      );
    }

    resumeTimer = window.setTimeout(
      function () {
        userIsInteracting = false;
        startAutoplay();
      },
      6000
    );
  }

  controls.forEach(function (control) {
    control.addEventListener(
      "click",
      function () {
        move(
          Number(
            control.getAttribute(
              "data-direction"
            )
          )
        );

        pauseForInteraction();
      }
    );
  });

  track.addEventListener(
    "scroll",
    updateUi,
    {
      passive: true,
    }
  );

  track.addEventListener(
    "pointerdown",
    pauseForInteraction
  );

  track.addEventListener(
    "touchstart",
    pauseForInteraction,
    {
      passive: true,
    }
  );

  shell.addEventListener(
    "mouseenter",
    function () {
      userIsInteracting = true;
      clearAutoplay();
    }
  );

  shell.addEventListener(
    "mouseleave",
    function () {
      userIsInteracting = false;
      startAutoplay();
    }
  );

  shell.addEventListener(
    "focusin",
    function () {
      userIsInteracting = true;
      clearAutoplay();
    }
  );

  shell.addEventListener(
    "focusout",
    function () {
      userIsInteracting = false;
      startAutoplay();
    }
  );

  if (autoplayButton) {
    autoplayButton.addEventListener(
      "click",
      function () {
        autoplayPaused =
          !autoplayPaused;

        const icon =
          autoplayButton.querySelector(
            "i"
          );

        const label =
          autoplayButton.querySelector(
            "span"
          );

        if (autoplayPaused) {
          clearAutoplay();

          autoplayButton.setAttribute(
            "aria-label",
            "Resume automatic tour slider"
          );

          if (icon) {
            icon.className =
              "fa-solid fa-play";
          }

          if (label) {
            label.textContent =
              "Play";
          }
        } else {
          autoplayButton.setAttribute(
            "aria-label",
            "Pause automatic tour slider"
          );

          if (icon) {
            icon.className =
              "fa-solid fa-pause";
          }

          if (label) {
            label.textContent =
              "Pause";
          }

          startAutoplay();
        }
      }
    );
  }

  document.addEventListener(
    "visibilitychange",
    function () {
      if (document.hidden) {
        clearAutoplay();
      } else {
        startAutoplay();
      }
    }
  );

  let resizeTimer;

  window.addEventListener(
    "resize",
    function () {
      window.clearTimeout(
        resizeTimer
      );

      resizeTimer =
        window.setTimeout(
          function () {
            updateUi();
            startAutoplay();
          },
          120
        );
    }
  );

  updateUi();
  startAutoplay();
});
