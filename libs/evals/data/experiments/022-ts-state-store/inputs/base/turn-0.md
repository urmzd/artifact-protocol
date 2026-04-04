Create a TypeScript state management store for a shopping cart application.

Include:
- Types: CartItem, Product, CartState, CartAction (union type)
- Action creators: addItem, removeItem, updateQuantity, applyCoupon, clearCart
- Reducer function handling all actions with immutable state updates
- Selectors: getCartTotal, getItemCount, getCartItems, getCouponDiscount, getTaxAmount
- Helper for localStorage persistence
