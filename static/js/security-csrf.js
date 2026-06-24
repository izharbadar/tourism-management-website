(function () {
  "use strict";

  function token() {
    const element = document.querySelector(
      'meta[name="csrf-token"]'
    );

    return element ? element.content : "";
  }

  function isUnsafe(method) {
    return ![
      "GET",
      "HEAD",
      "OPTIONS",
      "TRACE",
    ].includes(String(method || "GET").toUpperCase());
  }

  function isSameOrigin(url) {
    try {
      return new URL(url, window.location.href).origin
        === window.location.origin;
    } catch (error) {
      return false;
    }
  }

  document.addEventListener("submit", function (event) {
    const form = event.target;

    if (!(form instanceof HTMLFormElement)) {
      return;
    }

    if (!isUnsafe(form.method)) {
      return;
    }

    if (form.querySelector('input[name="csrf_token"]')) {
      return;
    }

    const csrfToken = token();

    if (!csrfToken) {
      return;
    }

    const hidden = document.createElement("input");
    hidden.type = "hidden";
    hidden.name = "csrf_token";
    hidden.value = csrfToken;
    form.appendChild(hidden);
  });

  if (window.fetch) {
    const originalFetch = window.fetch.bind(window);

    window.fetch = function (input, init) {
      const options = Object.assign({}, init || {});
      const requestMethod = options.method
        || (input instanceof Request ? input.method : "GET");
      const requestUrl = input instanceof Request
        ? input.url
        : input;

      if (isUnsafe(requestMethod) && isSameOrigin(requestUrl)) {
        const headers = new Headers(
          options.headers
          || (input instanceof Request ? input.headers : undefined)
        );

        if (!headers.has("X-CSRFToken")) {
          const csrfToken = token();

          if (csrfToken) {
            headers.set("X-CSRFToken", csrfToken);
          }
        }

        options.headers = headers;
        options.credentials = options.credentials || "same-origin";
      }

      return originalFetch(input, options);
    };
  }

  const originalOpen = XMLHttpRequest.prototype.open;
  const originalSend = XMLHttpRequest.prototype.send;

  XMLHttpRequest.prototype.open = function (method, url) {
    this._captureSecurityMethod = method;
    this._captureSecurityUrl = url;

    return originalOpen.apply(this, arguments);
  };

  XMLHttpRequest.prototype.send = function () {
    if (
      isUnsafe(this._captureSecurityMethod)
      && isSameOrigin(this._captureSecurityUrl)
    ) {
      const csrfToken = token();

      if (csrfToken) {
        this.setRequestHeader("X-CSRFToken", csrfToken);
      }
    }

    return originalSend.apply(this, arguments);
  };
})();
