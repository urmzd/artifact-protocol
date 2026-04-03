# Experiment: ts-react-form

**Format:** text/typescript | **Size:** medium | **Edits:** 3

**Expected sections:** types, validation, form-fields, summary, submission

## Protocol cost (the only difference from base)

| Prompt | Chars | ~Tokens |
|---|---|---|
| Base system | 96 | 24 |
| AAP init system | 239 | 59 |
| AAP maintain system | 859 | 214 |
| **Protocol overhead** | | **~250 tokens** |

## Turns

| Turn | Edit |
|---|---|
| 0 | (creation) |
| 1 | Add a new ShippingOption interface with fields: id, name, price, estimated_da... |
| 2 | Rewrite the form-fields section to add a promo code input with a 'Apply' butt... |
| 3 | Update the validation functions to show inline error messages below each fiel... |
