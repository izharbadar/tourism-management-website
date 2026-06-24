document.addEventListener("DOMContentLoaded", function () {
  const filterForm = document.getElementById(
    "reportFilterForm"
  );

  const customDates = document.getElementById(
    "reportCustomDates"
  );

  if (filterForm && customDates) {
    filterForm
      .querySelectorAll(
        'input[name="range"]'
      )
      .forEach(function (radio) {
        radio.addEventListener(
          "change",
          function () {
            filterForm
              .querySelectorAll(
                ".report-preset-option"
              )
              .forEach(function (label) {
                label.classList.remove(
                  "active"
                );
              });

            radio
              .closest(
                ".report-preset-option"
              )
              .classList.add("active");

            const isCustom =
              radio.value === "custom";

            customDates.classList.toggle(
              "show",
              isCustom
            );

            if (!isCustom) {
              filterForm.submit();
            }
          }
        );
      });
  }

  const dataNode = document.getElementById(
    "reportChartData"
  );

  const canvas = document.getElementById(
    "performanceChart"
  );

  const emptyState = document.getElementById(
    "performanceChartEmpty"
  );

  if (!dataNode || !canvas) {
    return;
  }

  let chartData;

  try {
    chartData = JSON.parse(
      dataNode.textContent
    );
  } catch (error) {
    console.error(
      "Could not parse report chart data.",
      error
    );
    return;
  }

  const bookings = (
    chartData.bookings || []
  );

  const revenue = (
    chartData.revenue || []
  );

  const hasData = (
    bookings.some(function (value) {
      return Number(value) > 0;
    })
    || revenue.some(function (value) {
      return Number(value) > 0;
    })
  );

  if (!hasData) {
    canvas.hidden = true;

    if (emptyState) {
      emptyState.hidden = false;
    }

    return;
  }

  const context = canvas.getContext("2d");

  function drawChart() {
    const ratio =
      window.devicePixelRatio || 1;

    const width =
      canvas.clientWidth;

    const height =
      canvas.clientHeight;

    canvas.width =
      Math.max(1, width * ratio);

    canvas.height =
      Math.max(1, height * ratio);

    context.setTransform(
      ratio,
      0,
      0,
      ratio,
      0,
      0
    );

    context.clearRect(
      0,
      0,
      width,
      height
    );

    const padding = {
      top: 18,
      right: 16,
      bottom: 38,
      left: 42,
    };

    const chartWidth =
      width
      - padding.left
      - padding.right;

    const chartHeight =
      height
      - padding.top
      - padding.bottom;

    const labels =
      chartData.labels || [];

    const maxBooking = Math.max(
      1,
      ...bookings.map(Number)
    );

    const maxRevenue = Math.max(
      1,
      ...revenue.map(Number)
    );

    context.strokeStyle =
      "#e4ece8";

    context.lineWidth = 1;

    context.fillStyle =
      "#7a8782";

    context.font =
      "9px Poppins, sans-serif";

    for (let index = 0; index <= 4; index += 1) {
      const y =
        padding.top
        + (
          chartHeight
          * index
          / 4
        );

      context.beginPath();

      context.moveTo(
        padding.left,
        y
      );

      context.lineTo(
        width - padding.right,
        y
      );

      context.stroke();

      const bookingLabel =
        Math.round(
          maxBooking
          * (4 - index)
          / 4
        );

      context.fillText(
        String(bookingLabel),
        8,
        y + 3
      );
    }

    function pointX(index) {
      if (labels.length <= 1) {
        return (
          padding.left
          + chartWidth / 2
        );
      }

      return (
        padding.left
        + chartWidth
        * index
        / (labels.length - 1)
      );
    }

    function bookingY(value) {
      return (
        padding.top
        + chartHeight
        - (
          Number(value)
          / maxBooking
          * chartHeight
        )
      );
    }

    function revenueY(value) {
      return (
        padding.top
        + chartHeight
        - (
          Number(value)
          / maxRevenue
          * chartHeight
        )
      );
    }

    function drawLine(
      values,
      yFunction,
      strokeColor,
      fillColor
    ) {
      context.beginPath();

      values.forEach(function (value, index) {
        const x = pointX(index);
        const y = yFunction(value);

        if (index === 0) {
          context.moveTo(x, y);
        } else {
          context.lineTo(x, y);
        }
      });

      context.strokeStyle =
        strokeColor;

      context.lineWidth = 2.4;

      context.lineJoin = "round";
      context.lineCap = "round";

      context.stroke();

      values.forEach(function (value, index) {
        const x = pointX(index);
        const y = yFunction(value);

        context.beginPath();

        context.arc(
          x,
          y,
          3,
          0,
          Math.PI * 2
        );

        context.fillStyle =
          fillColor;

        context.fill();
      });
    }

    drawLine(
      bookings,
      bookingY,
      "#0f7b65",
      "#0f7b65"
    );

    drawLine(
      revenue,
      revenueY,
      "#f7b733",
      "#f7b733"
    );

    const labelLimit =
      width < 620
      ? 5
      : 8;

    const labelStep = Math.max(
      1,
      Math.ceil(
        labels.length
        / labelLimit
      )
    );

    labels.forEach(function (label, index) {
      const shouldDraw = (
        index % labelStep === 0
        || index === labels.length - 1
      );

      if (!shouldDraw) {
        return;
      }

      const x = pointX(index);

      context.save();

      context.translate(
        x,
        height - 14
      );

      context.rotate(
        labels.length > 10
          ? -0.38
          : 0
      );

      context.textAlign =
        labels.length > 10
          ? "right"
          : "center";

      context.fillStyle =
        "#7a8782";

      context.font =
        "8px Poppins, sans-serif";

      context.fillText(
        label,
        0,
        0
      );

      context.restore();
    });
  }

  let resizeTimer;

  window.addEventListener(
    "resize",
    function () {
      window.clearTimeout(
        resizeTimer
      );

      resizeTimer =
        window.setTimeout(
          drawChart,
          100
        );
    }
  );

  drawChart();
});
