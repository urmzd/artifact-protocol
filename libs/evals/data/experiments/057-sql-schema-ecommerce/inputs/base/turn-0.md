Create a PostgreSQL schema for an e-commerce application.

Include:
- Tables: users, products, categories, orders, order_items, reviews, addresses, coupons, inventory
- Proper data types, constraints, foreign keys, NOT NULL, DEFAULT values
- Indexes: on foreign keys, email unique, composite indexes for common queries
- Views: order_summary (with totals), product_ratings (avg rating, count), low_stock_products
- Seed data: 5 categories, 10 products, 3 users, 5 sample orders with items
- Use SERIAL/BIGSERIAL for PKs, TIMESTAMPTZ for dates

