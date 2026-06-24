document.addEventListener("DOMContentLoaded", function () {
  const form = document.querySelector(
    "[data-manual-booking-form]"
  );

  function numberValue(element) {
    if (!element) {
      return 0;
    }

    const value = Number(
      String(element.value || "0")
        .replace(/,/g, "")
    );

    return Number.isFinite(value)
      ? value
      : 0;
  }

  function money(value) {
    return "PKR "
      + Math.max(value, 0).toLocaleString(
        "en-PK",
        {
          maximumFractionDigits: 0,
        }
      );
  }

  if (form) {
    const modeInputs = Array.from(
      form.querySelectorAll(
        'input[name="tour_mode"]'
      )
    );

    const existingFields = form.querySelector(
      "[data-existing-tour-fields]"
    );

    const customFields = form.querySelector(
      "[data-custom-tour-fields]"
    );

    const tourSelect = form.querySelector(
      "#tour_id"
    );

    const customTourInput = form.querySelector(
      "#custom_tour_name"
    );

    const pricingType = form.querySelector(
      "#pricing_type"
    );

    const quantity = form.querySelector(
      "#package_quantity"
    );

    const adults = form.querySelector(
      "#adults"
    );

    const children = form.querySelector(
      "#children"
    );

    const totalTravelers = form.querySelector(
      "#total_travelers"
    );

    const totalAmount = form.querySelector(
      "#total_amount"
    );

    const paidAmount = form.querySelector(
      "#paid_amount"
    );

    const paymentStatus = form.querySelector(
      "#payment_status"
    );

    const paymentMethod = form.querySelector(
      "#payment_method"
    );

    const customPaymentField = form.querySelector(
      "[data-custom-payment-field]"
    );

    const customPaymentInput = form.querySelector(
      "#custom_payment_method"
    );

    const quantityLabel = form.querySelector(
      "[data-quantity-label]"
    );

    const summaryTour = form.querySelector(
      "[data-summary-tour]"
    );

    const summaryTotal = form.querySelector(
      "[data-summary-total]"
    );

    const summaryPaid = form.querySelector(
      "[data-summary-paid]"
    );

    const summaryBalance = form.querySelector(
      "[data-summary-balance]"
    );

    function currentMode() {
      const checked = modeInputs.find(
        (input) => input.checked
      );

      return checked
        ? checked.value
        : "existing";
    }

    function updateMode() {
      const custom = currentMode() === "custom";

      existingFields.hidden = custom;
      customFields.hidden = !custom;

      tourSelect.required = !custom;
      customTourInput.required = custom;

      updateSummary();
    }

    function updateTravelers() {
      const pricing = pricingType.value;
      const count = Math.max(
        numberValue(quantity),
        1
      );

      quantityLabel.textContent = (
        pricing === "couple"
          ? "Number of Couples"
          : "Number of Persons"
      );

      if (
        document.activeElement !== adults
      ) {
        adults.value = (
          pricing === "couple"
            ? count * 2
            : count
        );
      }

      totalTravelers.value = (
        numberValue(adults)
        + numberValue(children)
      );

      updateSummary();
    }

    function updateAmounts() {
      const total = numberValue(
        totalAmount
      );

      const paid = Math.min(
        numberValue(paidAmount),
        total
      );

      const balance = Math.max(
        total - paid,
        0
      );

      summaryTotal.textContent = money(total);
      summaryPaid.textContent = money(paid);
      summaryBalance.textContent = money(
        balance
      );

      if (paid <= 0) {
        paymentStatus.value = "unpaid";
      } else if (paid < total) {
        paymentStatus.value = (
          "partially_paid"
        );
      } else if (total > 0) {
        paymentStatus.value = "paid";
      }
    }

    function updateSummary() {
      if (currentMode() === "custom") {
        summaryTour.textContent = (
          customTourInput.value.trim()
          || "Custom Tour"
        );
      } else {
        const option = (
          tourSelect.options[
            tourSelect.selectedIndex
          ]
        );

        summaryTour.textContent = (
          option && option.value
            ? option.textContent.trim()
            : "Choose a tour"
        );
      }

      updateAmounts();
    }

    function updatePaymentMethod() {
      const custom = (
        paymentMethod.value === "other"
      );

      customPaymentField.hidden = !custom;
      customPaymentInput.required = custom;
    }

    modeInputs.forEach(function (input) {
      input.addEventListener(
        "change",
        updateMode
      );
    });

    [
      tourSelect,
      customTourInput,
    ].forEach(function (element) {
      element.addEventListener(
        "input",
        updateSummary
      );

      element.addEventListener(
        "change",
        updateSummary
      );
    });

    [
      pricingType,
      quantity,
      adults,
      children,
    ].forEach(function (element) {
      element.addEventListener(
        "input",
        updateTravelers
      );

      element.addEventListener(
        "change",
        updateTravelers
      );
    });

    [
      totalAmount,
      paidAmount,
    ].forEach(function (element) {
      element.addEventListener(
        "input",
        updateAmounts
      );
    });

    paymentMethod.addEventListener(
      "change",
      updatePaymentMethod
    );

    updateMode();
    updateTravelers();
    updatePaymentMethod();
    updateSummary();
  }

  const updateForm = document.querySelector(
    "[data-payment-update-form]"
  );

  if (updateForm) {
    const total = updateForm.querySelector(
      "[data-update-total]"
    );

    const paid = updateForm.querySelector(
      "[data-update-paid]"
    );

    const balance = updateForm.querySelector(
      "[data-update-balance]"
    );

    const method = updateForm.querySelector(
      "[data-update-payment-method]"
    );

    const customMethod = updateForm.querySelector(
      "[data-update-custom-payment]"
    );

    function updateBalance() {
      balance.value = money(
        numberValue(total)
        - numberValue(paid)
      );
    }

    function updateCustomMethod() {
      customMethod.hidden = (
        method.value !== "other"
      );
    }

    total.addEventListener(
      "input",
      updateBalance
    );

    paid.addEventListener(
      "input",
      updateBalance
    );

    method.addEventListener(
      "change",
      updateCustomMethod
    );

    updateBalance();
    updateCustomMethod();
  }
});
