Create a Ruby on Rails model for an Order in an e-commerce application.

Include:
- Associations: belongs_to user, has_many order_items, has_one shipping_address, has_many payments
- Validations: presence, numericality, custom validators for status transitions
- Scopes: recent, by_status, by_date_range, high_value, pending_shipment
- Instance methods: total, subtotal, tax_amount, apply_coupon, can_cancel?, ship!, complete!
- State machine for order status (pending -> confirmed -> shipped -> delivered, with cancel)
- Callbacks: before_create, after_update
