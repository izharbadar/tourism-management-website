# Admin manual booking module

The live database must contain the manual-booking fields already added to the
local `bookings` table:

- `custom_tour_name`
- `custom_destination`
- `booking_source`
- `invoice_date`
- `paid_amount`
- `balance_amount`
- `custom_payment_method`

`bookings.user_id` and `bookings.tour_id` must remain `BIGINT UNSIGNED NULL`
when the related primary keys are unsigned. Export the fully working local
database after the migration; do not rerun old installer SQL on production.
