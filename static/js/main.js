document.addEventListener("DOMContentLoaded",()=>{const b=document.getElementById("menuBtn"),n=document.getElementById("mainNav");b?.addEventListener("click",()=>n.classList.toggle("open"));});

document.addEventListener("DOMContentLoaded", function () {
    const loginButton = document.getElementById("loginButton");
    const loginWrapper = document.querySelector(".login-wrapper");
    const siteHeader = document.getElementById("siteHeader");
    const mobileMenuBtn = document.getElementById("mobileMenuBtn");

    console.log("Header JavaScript loaded");

    // Login dropdown
    if (loginButton && loginWrapper) {
        loginButton.addEventListener("click", function (event) {
            event.preventDefault();
            event.stopPropagation();

            loginWrapper.classList.toggle("open");

            const isOpen = loginWrapper.classList.contains("open");
            loginButton.setAttribute("aria-expanded", isOpen);
        });
    } else {
        console.error("Login button or login wrapper not found");
    }

    // Dropdown ke andar click karne par close na ho
    if (loginWrapper) {
        loginWrapper.addEventListener("click", function (event) {
            event.stopPropagation();
        });
    }

    // Outside click par dropdown close
    document.addEventListener("click", function () {
        if (loginWrapper) {
            loginWrapper.classList.remove("open");
        }

        if (loginButton) {
            loginButton.setAttribute("aria-expanded", "false");
        }
    });

    // Mobile menu
    if (mobileMenuBtn && siteHeader) {
        mobileMenuBtn.addEventListener("click", function (event) {
            event.stopPropagation();

            siteHeader.classList.toggle("menu-open");

            const menuOpen = siteHeader.classList.contains("menu-open");
            mobileMenuBtn.setAttribute("aria-expanded", menuOpen);
        });
    }

    // Escape key par sab close
    document.addEventListener("keydown", function (event) {
        if (event.key === "Escape") {
            if (loginWrapper) {
                loginWrapper.classList.remove("open");
            }

            if (siteHeader) {
                siteHeader.classList.remove("menu-open");
            }
        }
    });
});




  document.addEventListener("DOMContentLoaded", function () {
    const profileMenus = document.querySelectorAll(
      "[data-profile-menu]"
    );




    

    profileMenus.forEach(function (profileMenu) {
      const trigger = profileMenu.querySelector(
        "[data-profile-trigger]"
      );

      if (!trigger) {
        return;
      }

      trigger.addEventListener("click", function (event) {
        event.preventDefault();
        event.stopPropagation();

        const isCurrentlyOpen =
          profileMenu.classList.contains("is-open");

        document
          .querySelectorAll("[data-profile-menu]")
          .forEach(function (otherMenu) {
            otherMenu.classList.remove("is-open");

            const otherTrigger = otherMenu.querySelector(
              "[data-profile-trigger]"
            );

            if (otherTrigger) {
              otherTrigger.setAttribute(
                "aria-expanded",
                "false"
              );
            }
          });

        if (!isCurrentlyOpen) {
          profileMenu.classList.add("is-open");
          trigger.setAttribute("aria-expanded", "true");
        }
      });
      // =========================================
// PASSWORD SHOW / HIDE
// =========================================

const passwordToggleButtons = document.querySelectorAll(
  "[data-password-toggle]"
);

passwordToggleButtons.forEach(function (button) {
  button.addEventListener("click", function () {
    const inputId = button.getAttribute(
      "data-password-toggle"
    );

    const passwordInput = document.getElementById(
      inputId
    );

    if (!passwordInput) {
      return;
    }

    const isPassword =
      passwordInput.type === "password";

    passwordInput.type = isPassword
      ? "text"
      : "password";

    button.textContent = isPassword
      ? "Hide"
      : "Show";
  });
});
    });

    document.addEventListener("click", function (event) {
      document
        .querySelectorAll("[data-profile-menu]")
        .forEach(function (profileMenu) {
          if (!profileMenu.contains(event.target)) {
            profileMenu.classList.remove("is-open");

            const trigger = profileMenu.querySelector(
              "[data-profile-trigger]"
            );

            if (trigger) {
              trigger.setAttribute(
                "aria-expanded",
                "false"
              );
            }
          }
        });
    });

    document.addEventListener("keydown", function (event) {
      if (event.key === "Escape") {
        document
          .querySelectorAll("[data-profile-menu]")
          .forEach(function (profileMenu) {
            profileMenu.classList.remove("is-open");

            const trigger = profileMenu.querySelector(
              "[data-profile-trigger]"
            );

            if (trigger) {
              trigger.setAttribute(
                "aria-expanded",
                "false"
              );
            }
          });
      }
    });
  });


  // =========================================
// PASSWORD SHOW / HIDE
// =========================================

document.addEventListener("click", function (event) {
  const toggleButton = event.target.closest(
    "[data-password-toggle]"
  );

  if (!toggleButton) {
    return;
  }

  event.preventDefault();

  const inputId = toggleButton.getAttribute(
    "data-password-toggle"
  );

  const passwordInput = document.getElementById(inputId);

  if (!passwordInput) {
    console.error(
      "Password field not found:",
      inputId
    );
    return;
  }

  const passwordIsHidden =
    passwordInput.type === "password";

  passwordInput.type = passwordIsHidden
    ? "text"
    : "password";

  toggleButton.textContent = passwordIsHidden
    ? "Hide"
    : "Show";
});