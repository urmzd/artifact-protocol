Create a TypeScript state management store for a shopping cart application.

Include:
- Types: CartItem, Product, CartState, CartAction (union type)
- Action creators: addItem, removeItem, updateQuantity, applyCoupon, clearCart
- Reducer function handling all actions with immutable state updates
- Selectors: getCartTotal, getItemCount, getCartItems, getCouponDiscount, getTaxAmount
- Helper for localStorage persistence

Use section IDs: types, actions, reducers, selectors

Use AAP section markers to delineate each major code block.
Wrap each logical section with `<aap:section id="ID">` and `</aap:section>`.


Output raw code only. No markdown fences, no explanation.