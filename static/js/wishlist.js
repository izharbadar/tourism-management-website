document.addEventListener("DOMContentLoaded", function () {
  const forms = document.querySelectorAll(
    "[data-wishlist-form]"
  );

  if (!forms.length) {
    return;
  }

  function showToast(message, isError) {
    let toast = document.querySelector(
      "[data-wishlist-toast]"
    );

    if (!toast) {
      toast = document.createElement("div");
      toast.className = "wishlist-toast";
      toast.setAttribute(
        "data-wishlist-toast",
        ""
      );
      document.body.appendChild(toast);
    }

    toast.textContent = message;
    toast.classList.toggle(
      "is-error",
      Boolean(isError)
    );
    toast.classList.add("is-visible");

    window.clearTimeout(
      toast.hideTimer
    );

    toast.hideTimer = window.setTimeout(
      function () {
        toast.classList.remove(
          "is-visible"
        );
      },
      2800
    );
  }

  function updateButtons(tourId, saved) {
    document
      .querySelectorAll(
        `[data-wishlist-button][data-tour-id="${tourId}"]`
      )
      .forEach(function (button) {
        const heart = button.querySelector(
          ".wishlist-heart"
        );
        const label = button.querySelector(
          ".wishlist-button-label"
        );

        button.classList.toggle(
          "is-saved",
          saved
        );
        button.setAttribute(
          "aria-pressed",
          saved ? "true" : "false"
        );

        if (heart) {
          heart.textContent = saved
            ? "♥"
            : "♡";
        }

        if (label) {
          label.textContent = saved
            ? "Saved"
            : "Save";
        }
      });
  }

  function updateCount(count) {
    document
      .querySelectorAll(
        "[data-wishlist-count]"
      )
      .forEach(function (element) {
        element.textContent = count;
      });
  }

  function removeWishlistCard(tourId) {
    const card = document.querySelector(
      `[data-wishlist-card="${tourId}"]`
    );

    if (!card) {
      return;
    }

    card.style.opacity = "0";
    card.style.transform = "scale(0.97)";

    window.setTimeout(function () {
      card.remove();

      const grid = document.querySelector(
        "[data-wishlist-grid]"
      );
      const empty = document.querySelector(
        "[data-wishlist-empty]"
      );

      if (
        grid
        && !grid.querySelector(
          "[data-wishlist-card]"
        )
      ) {
        grid.hidden = true;

        if (empty) {
          empty.hidden = false;
        }
      }
    }, 220);
  }

  forms.forEach(function (form) {
    form.addEventListener(
      "submit",
      async function (event) {
        event.preventDefault();

        const button = form.querySelector(
          "[data-wishlist-button]"
        );

        if (!button) {
          form.submit();
          return;
        }

        const tourId = button.getAttribute(
          "data-tour-id"
        );

        button.classList.add(
          "is-loading"
        );
        button.disabled = true;

        try {
          const response = await fetch(
            form.action,
            {
              method: "POST",
              body: new FormData(form),
              headers: {
                "X-Requested-With":
                  "XMLHttpRequest",
                Accept: "application/json",
              },
            }
          );

          const data = await response.json();

          if (
            response.status === 401
            && data.login_url
          ) {
            window.location.href = (
              data.login_url
            );
            return;
          }

          if (!response.ok || !data.ok) {
            throw new Error(
              data.message
              || "Wishlist could not be updated."
            );
          }

          updateButtons(
            String(data.tour_id),
            data.saved
          );
          updateCount(
            data.wishlist_count
          );

          if (!data.saved) {
            removeWishlistCard(
              String(data.tour_id)
            );
          }

          showToast(
            data.message,
            false
          );

        } catch (error) {
          showToast(
            error.message
            || "Wishlist could not be updated.",
            true
          );

        } finally {
          button.classList.remove(
            "is-loading"
          );
          button.disabled = false;
        }
      }
    );
  });
});
