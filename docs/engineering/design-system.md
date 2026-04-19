# Design System

Asian Auntie is a mobile-first pantry tracker. The visual design should feel clean and purposeful — not decorative. No emojis in UI chrome.

---

## Colour Palette

Two colours only. Everything derives from them.

| Role           | Name           | Hex                   | Use                                                          |
| -------------- | -------------- | --------------------- | ------------------------------------------------------------ |
| Background     | Pale Amber     | `#CFD78C`             | Page background — the canvas                                 |
| Text / primary | Crimson Violet | `#700143`             | All body text, headings, links, buttons                      |
| Primary hover  | —              | `#56022f`             | Pressed/hovered state                                        |
| Muted text     | —              | `rgba(112,1,67,0.55)` | Secondary labels, hints — translucent crimson, not grey      |
| Card           | White          | `#ffffff`             | Cards and form containers only — keeps form content readable |
| Nav            | Crimson Violet | `#700143`             | Nav bar background (inverted: amber text on crimson)         |

Semantic urgency colours are the only exception — they carry meaning that would be lost if mapped to the brand palette:

| State             | Colour    |
| ----------------- | --------- |
| Urgent (today)    | `#c0392b` |
| Warning (≤2 days) | `#d97706` |
| Expired           | `#718096` |

### Why this approach

The two brand colours appear everywhere, exclusively. No neutral greys, no warm-white surfaces — those dilute the palette. The nav inverts the pair (crimson background, amber text) to create clear separation between app shell and content without introducing a third colour.

---

## Typography

**Font: Plus Jakarta Sans** — loaded from Google Fonts.

```
weights: 400 (body), 500 (labels), 600 (card names, subheadings), 700 (brand, badges)
```

| Scale | Usage                     | Size / Weight        |
| ----- | ------------------------- | -------------------- |
| Brand | Nav brand name            | 1rem / 700           |
| H2    | Page titles               | 1.5rem / 600         |
| Body  | Form labels, descriptions | 1rem / 400           |
| Small | Badges, hints, errors     | 0.8–0.9rem / 500–700 |

**Why Plus Jakarta Sans:**

- Humanist-geometric hybrid — warm but structured
- Excellent legibility at small sizes on mobile screens
- Slightly elevated x-height keeps it readable at 14–16px
- Pairs well with the earthy palette without adding a heritage or decorative feel

**Alignment rules:**

- All body text: left-aligned
- Auth cards: centred on screen, left-aligned text within the card
- Badges/urgency labels: left-aligned, uppercase, tight letter-spacing
- Buttons: centred text within the button
- Never centre-align paragraph text or form labels

---

## Spacing

Base unit: 4px. Use multiples: 4, 8, 12, 16, 24, 32, 48.

- Component internal padding: 16px (1rem)
- Section gaps: 24px (1.5rem)
- Form field spacing: 8px between label and input; 16px between fields
- Grid gap: 12px on mobile, 16px on larger screens

---

## Layout

Mobile-first. The primary target is a phone held in one hand.

- Max content width: 480px on mobile, 600px on tablet
- Container horizontal padding: 16px on mobile, 24px on larger
- Nav: amber accent line at bottom (2px solid), scrolls with page — do not make it sticky without a full-bleed wrapper outside `.container`
- Cards: white background, 10px border radius, subtle shadow on hover
- Tap targets: minimum 44px height for all interactive elements

---

## Components

### Nav bar

- Brand name: left, crimson violet, 700 weight, no emoji
- Primary action (Add item): right, compact, plain link
- Log out: right, small outlined button
- Bottom border: 2px solid pale amber (`#CFD78C`) — the single decorative element
- Background: white with slight shadow when scrolled (via `sticky`)

### Item cards

Three urgency tiers, communicated via a left border stripe:

| State          | Left border         | Badge colour |
| -------------- | ------------------- | ------------ |
| Today          | `#c0392b` (red)     | red          |
| Soon (≤2 days) | `#d97706` (amber)   | amber        |
| OK             | `#e5e7eb` (neutral) | muted grey   |

Cards use a white background. On hover: shadow deepens slightly. No colour fill changes.

### Buttons

- Primary action: crimson violet fill, white text (`class="contrast"` in Pico)
- Secondary: outlined, grey
- Destructive confirm: secondary outlined, not red — relies on placement and copy to communicate intent
- Minimum tap target: 44px height

### Form fields

- Labels: 500 weight, left-aligned, no colon
- Inputs: standard Pico styled; crimson violet focus ring
- Error text: red, small, appears directly below the field
- Hint text: muted grey, 0.9rem, below the field

### Urgency marks (detail view)

Inline `<mark>` badges with coloured backgrounds and white text. Padding: 2px 6px. Border radius: 4px.

---

## What to avoid

- Emojis in navigation, headings, or buttons
- Centred body text or form labels
- Multiple colours on the same page section — use the palette sparingly
- Card backgrounds other than white (`#ffffff`)
- Hover effects that change card background colour (shadow only)

---

## Implementation notes

PicoCSS v2 is the base framework. Override its custom properties in `:root`:

```css
--pico-primary: #700143;
--pico-primary-hover: #56022f;
--pico-primary-inverse: #ffffff;
--pico-font-family: "Plus Jakarta Sans", system-ui, sans-serif;
--pico-background-color: #f9f8f5;
```

Do not fork or eject from PicoCSS. Extend via `style.css` only.

---

**Last updated:** 2026-04-19
