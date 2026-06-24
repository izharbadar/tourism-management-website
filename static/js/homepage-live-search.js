document.addEventListener("DOMContentLoaded", function () {
  const searchRoot = document.querySelector(
    "[data-tour-live-search]"
  );

  if (!searchRoot) {
    return;
  }

  const form = searchRoot.closest(
    "form"
  );

  const input = searchRoot.querySelector(
    ".live-tour-search-input"
  );

  const clearButton = searchRoot.querySelector(
    "[data-live-search-clear]"
  );

  const dropdown = searchRoot.querySelector(
    "[data-live-search-dropdown]"
  );

  const loading = searchRoot.querySelector(
    "[data-live-search-loading]"
  );

  const results = searchRoot.querySelector(
    "[data-live-search-results]"
  );

  const viewAll = searchRoot.querySelector(
    "[data-live-search-view-all]"
  );

  const endpoint = searchRoot.dataset.searchEndpoint;
  const allToursUrl = searchRoot.dataset.allToursUrl;

  let debounceTimer = null;
  let abortController = null;
  let activeIndex = -1;
  let resultButtons = [];
  let lastQuery = null;

  function openDropdown() {
    dropdown.hidden = false;
    input.setAttribute(
      "aria-expanded",
      "true"
    );
  }

  function closeDropdown() {
    dropdown.hidden = true;
    input.setAttribute(
      "aria-expanded",
      "false"
    );

    activeIndex = -1;
    updateActiveResult();
  }

  function setLoading(isLoading) {
    loading.hidden = !isLoading;

    if (isLoading) {
      openDropdown();
    }
  }

  function updateClearButton() {
    clearButton.hidden = (
      input.value.trim() === ""
    );
  }

  function clearResults() {
    results.replaceChildren();
    resultButtons = [];
    activeIndex = -1;
  }

  function formatPrice(value) {
    return new Intl.NumberFormat(
      "en-PK",
      {
        maximumFractionDigits: 0,
      }
    ).format(
      Number(value || 0)
    );
  }

  function createSectionHeading(
    iconClass,
    title
  ) {
    const heading = document.createElement(
      "div"
    );

    heading.className =
      "live-tour-search-section-heading";

    const icon = document.createElement(
      "i"
    );

    icon.className = iconClass;

    const text = document.createElement(
      "span"
    );

    text.textContent = title;

    heading.append(
      icon,
      text
    );

    return heading;
  }

  function createDestinationResult(
    destination
  ) {
    const button = document.createElement(
      "button"
    );

    button.type = "button";
    button.className =
      "live-tour-search-result destination-result";

    button.dataset.url =
      destination.url;

    button.setAttribute(
      "role",
      "option"
    );

    const imageWrap =
      document.createElement(
        "span"
      );

    imageWrap.className =
      "live-search-result-image destination-image";

    const image = document.createElement(
      "img"
    );

    image.src = destination.image;
    image.alt = "";
    image.loading = "lazy";

    image.addEventListener(
      "error",
      function () {
        imageWrap.replaceChildren();

        const fallback =
          document.createElement(
            "i"
          );

        fallback.className =
          "fa-solid fa-location-dot";

        imageWrap.appendChild(
          fallback
        );
      },
      {
        once: true,
      }
    );

    imageWrap.appendChild(image);

    const content = document.createElement(
      "span"
    );

    content.className =
      "live-search-result-content";

    const title = document.createElement(
      "strong"
    );

    title.textContent =
      destination.name;

    const meta = document.createElement(
      "small"
    );

    const tourWord = (
      Number(
        destination.tour_count
      ) === 1
        ? "tour"
        : "tours"
    );

    meta.textContent = (
      destination.tour_count
      + " "
      + tourWord
      + " available"
    );

    content.append(
      title,
      meta
    );

    const arrow = document.createElement(
      "i"
    );

    arrow.className =
      "fa-solid fa-arrow-right live-search-result-arrow";

    button.append(
      imageWrap,
      content,
      arrow
    );

    return button;
  }

  function createTourResult(tour) {
    const button = document.createElement(
      "button"
    );

    button.type = "button";
    button.className =
      "live-tour-search-result tour-result";

    button.dataset.url = tour.url;

    button.setAttribute(
      "role",
      "option"
    );

    const imageWrap =
      document.createElement(
        "span"
      );

    imageWrap.className =
      "live-search-result-image";

    const image = document.createElement(
      "img"
    );

    image.src = tour.image;
    image.alt = "";
    image.loading = "lazy";

    imageWrap.appendChild(image);

    const content = document.createElement(
      "span"
    );

    content.className =
      "live-search-result-content";

    const title = document.createElement(
      "strong"
    );

    title.textContent = tour.title;

    const meta = document.createElement(
      "small"
    );

    const duration = (
      Number(tour.duration_days)
      + " "
      + (
        Number(tour.duration_days) === 1
          ? "day"
          : "days"
      )
    );

    meta.textContent = (
      tour.destination
      + " · "
      + duration
      + " · "
      + tour.category
    );

    content.append(
      title,
      meta
    );

    const price = document.createElement(
      "span"
    );

    price.className =
      "live-search-result-price";

    const priceLabel =
      document.createElement(
        "small"
      );

    priceLabel.textContent =
      "From";

    const priceValue =
      document.createElement(
        "strong"
      );

    priceValue.textContent = (
      tour.currency
      + " "
      + formatPrice(
        tour.price
      )
    );

    price.append(
      priceLabel,
      priceValue
    );

    button.append(
      imageWrap,
      content,
      price
    );

    return button;
  }

  function createEmptyState(query) {
    const empty = document.createElement(
      "div"
    );

    empty.className =
      "live-tour-search-empty";

    const icon = document.createElement(
      "span"
    );

    icon.innerHTML =
      '<i class="fa-solid fa-map-location-dot"></i>';

    const title = document.createElement(
      "strong"
    );

    title.textContent =
      "No matching tours found";

    const text = document.createElement(
      "p"
    );

    text.textContent = query
      ? (
          'Try another destination or tour name for "'
          + query
          + '".'
        )
      : (
          "Published tours will appear here automatically."
        );

    empty.append(
      icon,
      title,
      text
    );

    return empty;
  }

  function updateActiveResult() {
    resultButtons.forEach(
      function (button, index) {
        const isActive = (
          index === activeIndex
        );

        button.classList.toggle(
          "is-active",
          isActive
        );

        button.setAttribute(
          "aria-selected",
          isActive
            ? "true"
            : "false"
        );

        if (isActive) {
          button.scrollIntoView({
            block: "nearest",
          });
        }
      }
    );
  }

  function navigateToResult(button) {
    if (
      button
      && button.dataset.url
    ) {
      window.location.href =
        button.dataset.url;
    }
  }

  function bindResultButtons() {
    resultButtons = Array.from(
      results.querySelectorAll(
        ".live-tour-search-result"
      )
    );

    resultButtons.forEach(
      function (button, index) {
        button.addEventListener(
          "mouseenter",
          function () {
            activeIndex = index;
            updateActiveResult();
          }
        );

        button.addEventListener(
          "click",
          function () {
            navigateToResult(
              button
            );
          }
        );
      }
    );
  }

  function renderResponse(data) {
    clearResults();

    const destinations =
      Array.isArray(
        data.destinations
      )
        ? data.destinations
        : [];

    const tours =
      Array.isArray(
        data.tours
      )
        ? data.tours
        : [];

    if (tours.length) {
      results.appendChild(
        createSectionHeading(
          "fa-solid fa-ticket",
          data.query
            ? "Matching tours"
            : "Popular tours"
        )
      );

      tours.forEach(
        function (tour) {
          results.appendChild(
            createTourResult(
              tour
            )
          );
        }
      );
    }

    if (destinations.length) {
      results.appendChild(
        createSectionHeading(
          "fa-solid fa-location-dot",
          data.query
            ? "Matching destinations"
            : "Popular destinations"
        )
      );

      destinations.forEach(
        function (destination) {
          results.appendChild(
            createDestinationResult(
              destination
            )
          );
        }
      );
    }

    if (
      !destinations.length
      && !tours.length
    ) {
      results.appendChild(
        createEmptyState(
          data.query || ""
        )
      );
    }

    const searchValue =
      input.value.trim();

    viewAll.href = searchValue
      ? (
          allToursUrl
          + "?search="
          + encodeURIComponent(
              searchValue
            )
        )
      : allToursUrl;

    bindResultButtons();
    openDropdown();
  }

  async function fetchSuggestions(
    query
  ) {
    if (
      query === lastQuery
      && !dropdown.hidden
    ) {
      return;
    }

    lastQuery = query;

    if (abortController) {
      abortController.abort();
    }

    abortController =
      new AbortController();

    setLoading(true);

    try {
      const response = await fetch(
        endpoint
        + "?q="
        + encodeURIComponent(query),
        {
          headers: {
            Accept: "application/json",
          },
          signal:
            abortController.signal,
        }
      );

      if (!response.ok) {
        throw new Error(
          "Search request failed."
        );
      }

      const data =
        await response.json();

      renderResponse(data);
    } catch (error) {
      if (
        error.name
        === "AbortError"
      ) {
        return;
      }

      clearResults();

      const failed =
        document.createElement(
          "div"
        );

      failed.className =
        "live-tour-search-empty";

      failed.innerHTML = (
        '<span><i class="fa-solid fa-triangle-exclamation"></i></span>'
        + "<strong>Search is temporarily unavailable</strong>"
        + "<p>You can still browse all published tours.</p>"
      );

      results.appendChild(
        failed
      );

      openDropdown();
    } finally {
      setLoading(false);
    }
  }

  function scheduleSearch() {
    window.clearTimeout(
      debounceTimer
    );

    const query =
      input.value.trim();

    updateClearButton();

    debounceTimer =
      window.setTimeout(
        function () {
          fetchSuggestions(
            query
          );
        },
        220
      );
  }

  input.addEventListener(
    "focus",
    function () {
      fetchSuggestions(
        input.value.trim()
      );
    }
  );

  input.addEventListener(
    "input",
    scheduleSearch
  );

  input.addEventListener(
    "keydown",
    function (event) {
      if (
        event.key === "ArrowDown"
      ) {
        event.preventDefault();

        if (dropdown.hidden) {
          fetchSuggestions(
            input.value.trim()
          );

          return;
        }

        if (!resultButtons.length) {
          return;
        }

        activeIndex = (
          activeIndex + 1
        ) % resultButtons.length;

        updateActiveResult();
      }

      if (
        event.key === "ArrowUp"
      ) {
        event.preventDefault();

        if (!resultButtons.length) {
          return;
        }

        activeIndex = (
          activeIndex <= 0
            ? resultButtons.length - 1
            : activeIndex - 1
        );

        updateActiveResult();
      }

      if (
        event.key === "Enter"
        && activeIndex >= 0
      ) {
        event.preventDefault();

        navigateToResult(
          resultButtons[
            activeIndex
          ]
        );
      }

      if (event.key === "Escape") {
        closeDropdown();
        input.blur();
      }
    }
  );

  clearButton.addEventListener(
    "click",
    function () {
      input.value = "";
      updateClearButton();
      input.focus();
      fetchSuggestions("");
    }
  );

  document.addEventListener(
    "click",
    function (event) {
      if (
        !searchRoot.contains(
          event.target
        )
      ) {
        closeDropdown();
      }
    }
  );

  form.addEventListener(
    "submit",
    function (event) {
      if (
        activeIndex >= 0
        && resultButtons[
          activeIndex
        ]
      ) {
        event.preventDefault();

        navigateToResult(
          resultButtons[
            activeIndex
          ]
        );
      }
    }
  );

  updateClearButton();
});
