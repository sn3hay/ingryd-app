# Ingryd — Style Guide

> Single source of truth for visual design, component patterns, and code conventions.
> Drop this into any AI coding session (Claude, Cursor, etc.) so output stays consistent regardless of who's building.

---

## 1. Color System

### Core Palette

| Token          | Hex       | Role                                              |
| -------------- | --------- | ------------------------------------------------- |
| `ink`          | `#09090B` | Primary text, dark surfaces, icons                 |
| `rose`         | `#DBAEBB` | Brand accent — buttons, links, active states       |
| `sage`         | `#8F9951` | Secondary accent — beneficial badges, success cues |
| `stone`        | `#D6D6D1` | Neutral — borders, dividers, muted text            |

### Extended Tints & Shades

Derived from the core four. Use these for hover states, backgrounds, and layering — never eyeball a one-off hex.

| Token            | Hex       | Usage                                    |
| ---------------- | --------- | ---------------------------------------- |
| `ink-light`      | `#18181B` | Elevated dark surface (cards on dark bg) |
| `ink-muted`      | `#27272A` | Secondary text on dark backgrounds       |
| `rose-soft`      | `#F2E6EA` | Rose tint background (cards, highlights) |
| `rose-hover`     | `#D0A0AE` | Button / link hover                      |
| `rose-pressed`   | `#C48D9C` | Button active / pressed                  |
| `sage-soft`      | `#EFF1E6` | Sage tint background (benefit badges)    |
| `sage-hover`     | `#7D8847` | Hover on sage elements                   |
| `sage-dark`      | `#5E6636` | Text on sage-soft backgrounds            |
| `stone-light`    | `#F0F0ED` | Page background                          |
| `stone-hover`    | `#C8C8C2` | Divider / border hover                   |
| `stone-dark`     | `#A1A19B` | Placeholder text, disabled states        |

### Semantic / Score Colors

Used exclusively for the ingredient scoring system and UI feedback states.

| Token          | Hex       | Grade / State              |
| -------------- | --------- | -------------------------- |
| `score-excellent` | `#5A7A2E` | Score 80–100 (Excellent) |
| `score-good`     | `#8F9951` | Score 60–79 (Good) — same as `sage` |
| `score-fair`     | `#BFA24E` | Score 40–59 (Fair)       |
| `score-poor`     | `#BF7A3D` | Score 20–39 (Poor)       |
| `score-avoid`    | `#BF4040` | Score 0–19 (Avoid)       |
| `error`          | `#BF4040` | Form validation, API errors — same as `score-avoid` |
| `warning`        | `#BFA24E` | Caution states — same as `score-fair` |
| `info`           | `#5B7FA6` | Informational banners, tooltips |

### Applying Colors

- **Light mode (default):** `stone-light` page background, white (`#FFFFFF`) card surfaces, `ink` text.
- **Dark mode (future):** `ink` page background, `ink-light` card surfaces, `stone` primary text, `stone-dark` secondary text.
- Rose is the primary interaction color. Every tappable element that isn't a destructive action uses rose or its variants.
- Sage appears only where something is positive — beneficial ingredients, good scores, success toasts.
- Never use score colors for non-score UI. A green button that isn't confirming a "good" score is confusing in this app.

---

## 2. Typography

### Typefaces

| Face       | Source    | Role                                         |
| ---------- | --------- | -------------------------------------------- |
| **Stardom** | [Fontshare](https://www.fontshare.com/fonts/stardom) | Display — logo, page titles (h1), hero text, the score grade label |
| **Inter**   | [Google Fonts](https://fonts.google.com/specimen/Inter) | Everything else — body, UI labels, buttons, inputs, captions |

Stardom is single-weight (400). Do not fake-bold it — it's a display face and should always feel light and elegant. If something needs emphasis alongside Stardom, use Inter Semibold or Bold instead.

### Type Scale

Built on a base of `16px` with a `1.25` ratio. All values in `rem`.

| Level     | Face    | Size       | Weight | Line height | Letter spacing | Usage                        |
| --------- | ------- | ---------- | ------ | ----------- | -------------- | ---------------------------- |
| `display` | Stardom | `2.441rem` | 400    | 1.1         | `-0.02em`      | Hero headlines, landing page |
| `h1`      | Stardom | `1.953rem` | 400    | 1.15        | `-0.01em`      | Page titles                  |
| `h2`      | Inter   | `1.563rem` | 600    | 1.25        | `-0.01em`      | Section headings             |
| `h3`      | Inter   | `1.25rem`  | 600    | 1.3         | `0`            | Card titles, sub-sections    |
| `h4`      | Inter   | `1rem`     | 600    | 1.4         | `0`            | Labels, group headers        |
| `body`    | Inter   | `1rem`     | 400    | 1.6         | `0`            | Paragraphs, descriptions     |
| `body-sm` | Inter   | `0.875rem` | 400    | 1.5         | `0`            | Secondary info, metadata     |
| `caption` | Inter   | `0.75rem`  | 500    | 1.4         | `0.01em`       | Timestamps, footnotes        |
| `score`   | Stardom | `3.052rem` | 400    | 1.0         | `-0.02em`      | The big score number (0–100) |

### Rules

- Maximum line length: **65 characters** for body text. Use `max-w-prose` or equivalent.
- Stardom is for display only — never use it below `1.25rem` or for paragraph text.
- Prefer sentence case everywhere. No ALL CAPS for labels or buttons.
- One typeface per element. Don't mix Stardom and Inter within the same heading.

---

## 3. Spacing & Layout

### Base Unit

`4px` (`0.25rem`). All spacing is a multiple of this unit.

| Token  | Value   | Common use                         |
| ------ | ------- | ---------------------------------- |
| `xs`   | `4px`   | Inline icon gap, tight padding     |
| `sm`   | `8px`   | Badge padding, compact gaps        |
| `md`   | `16px`  | Card internal padding, list gaps   |
| `lg`   | `24px`  | Section gaps, card outer margin    |
| `xl`   | `32px`  | Page section separation            |
| `2xl`  | `48px`  | Major section breaks               |
| `3xl`  | `64px`  | Page top/bottom padding            |

### Layout

- **Max content width:** `640px` for single-column flows (scan result, product detail). `1024px` for comparison / grid views.
- **Page padding:** `16px` horizontal on mobile, `24px` on tablet+.
- **Card padding:** `16px` on mobile, `20px` on desktop.
- **Content is left-aligned** by default. Center-align only the score display and empty states.

### Border Radius

| Token       | Value  | Usage                               |
| ----------- | ------ | ----------------------------------- |
| `radius-sm` | `6px`  | Badges, chips, small tags           |
| `radius-md` | `12px` | Cards, inputs, buttons              |
| `radius-lg` | `16px` | Modals, bottom sheets               |
| `radius-full` | `9999px` | Avatars, score circle, pill shapes |

---

## 4. Shadows & Elevation

Keep shadows minimal — this isn't a layered dashboard. Two levels are enough.

| Token       | Value                                  | Usage               |
| ----------- | -------------------------------------- | -------------------- |
| `shadow-sm` | `0 1px 3px rgba(9, 9, 11, 0.06)`      | Cards at rest        |
| `shadow-md` | `0 4px 12px rgba(9, 9, 11, 0.08)`     | Modals, popovers, elevated cards |

No shadow on buttons. Buttons use background color shift for depth.

---

## 5. Component Patterns

These are not a component library — they're constraints so AI-generated output stays visually coherent.

### Buttons

| Variant     | Background        | Text        | Border              | Use for                            |
| ----------- | ----------------- | ----------- | -------------------- | ---------------------------------- |
| Primary     | `rose`            | `#FFFFFF`   | none                 | Main CTA — "Scan", "Analyse"      |
| Secondary   | transparent       | `rose`      | `1px solid rose`     | Secondary actions — "Compare", "Save" |
| Ghost       | transparent       | `ink`       | none                 | Tertiary — "Cancel", "Back"        |
| Destructive | `score-avoid`     | `#FFFFFF`   | none                 | Dangerous — "Delete routine"       |

- Height: `44px` min (touch target).
- Padding: `12px 24px`.
- Radius: `radius-md` (`12px`).
- Font: Inter, `0.875rem`, weight 600.
- Hover: shift to respective `-hover` token. Transition: `150ms ease`.
- Disabled: `0.5` opacity, `cursor: not-allowed`.

### Inputs

- Height: `44px`.
- Background: `#FFFFFF` (light mode), `ink-light` (dark mode).
- Border: `1px solid stone`, `radius-md`.
- Focus ring: `2px` offset ring in `rose-soft`.
- Placeholder text: `stone-dark`.
- Error state: border becomes `error`, helper text below in `error` color.

### Cards

- Background: `#FFFFFF`.
- Border: `1px solid stone` (or no border + `shadow-sm`; pick one per screen, don't mix).
- Radius: `radius-md`.
- Padding: `md` (`16px`).
- No nested cards. If you need hierarchy inside a card, use background tint (`rose-soft`, `sage-soft`, `stone-light`).

### Product Result Card

The primary data display after a scan or search.

```
┌──────────────────────────────────────────┐
│  [Product Image]   Product Name          │
│   80 × 80px        Brand · Category      │
│   radius-sm         body-sm, stone-dark   │
│                                          │
│  ┌─── Score Block (center-aligned) ────┐ │
│  │  72          Good                   │ │
│  │  score size  h3, score-good color   │ │
│  │  ──────────── progress bar ──────── │ │
│  └─────────────────────────────────────┘ │
│                                          │
│  Ingredient Breakdown                    │
│  🔴 High concern (3)     [expandable]    │
│  🟡 Moderate concern (2) [expandable]    │
│  🟢 Beneficial (5)       [expandable]    │
│                                          │
│  [ Full ingredient list — collapsible ]  │
└──────────────────────────────────────────┘
```

- Concern dots use score colors, not emoji — render as small filled circles (`8px`, `radius-full`).
- Ingredient chips inside expanded sections: `sage-soft` bg for beneficial, `rose-soft` bg for concerns, `stone-light` bg for neutral.

### Score Bar

- Height: `8px`, `radius-full`.
- Track: `stone`.
- Fill: gradient from `score-avoid` → `score-fair` → `score-good` → `score-excellent`, clipped to the score percentage.
- Always accompanied by the numeric score (`score` type size) and grade label (`h3`).

### Navigation

- Bottom tab bar on mobile (Scan, Search, Routine, Profile).
- Active tab icon + label in `rose`; inactive in `stone-dark`.
- No top nav bar — page titles sit inside the content area as `h1`.

### Empty States

- Centered layout.
- Illustration or icon in `stone` / `stone-dark`, max `120px`.
- One line of heading (`h3`), one line of body copy, one primary button.
- Tone: direct and helpful, never cute ("No products scanned yet. Tap Scan to check your first product.")

### Loading & Skeleton

- Skeleton rectangles in `stone` with a subtle shimmer animation (`1.5s ease-in-out infinite`).
- Match skeleton shapes to the content they replace (image placeholder = square, text = rounded bars).
- For API lookups after a scan, show the product image + name immediately (from barcode DB), skeleton the score and ingredients.

---

## 6. Iconography

| Property     | Value                |
| ------------ | -------------------- |
| Library      | [Lucide React](https://lucide.dev/) |
| Default size | `20px` (mobile), `20px` (desktop) |
| Stroke width | `1.75`               |
| Style        | Outline only — no filled variants |
| Color        | Inherits text color   |

Use icons to reinforce meaning, not as decoration. Every icon should have a visible text label or an `aria-label`.

---

## 7. Motion

| Property              | Value                     |
| --------------------- | ------------------------- |
| Micro transitions     | `150ms ease`              |
| Layout transitions    | `250ms ease-out`          |
| Page transitions      | `300ms ease-in-out`       |
| Skeleton shimmer      | `1.5s ease-in-out infinite` |
| Easing (default)      | `cubic-bezier(0.4, 0, 0.2, 1)` |
| Reduced motion        | Respect `prefers-reduced-motion: reduce` — disable all non-essential animation |

Only one entrance animation per page load. Ingredient breakdown expanding/collapsing is the primary interactive motion. Everything else is color/opacity transitions.

---

## 8. Copy & Tone

Ingryd speaks like a knowledgeable friend, not a dermatologist's intake form.

| Do                                        | Don't                                    |
| ----------------------------------------- | ---------------------------------------- |
| "Contains 3 high-concern ingredients"     | "WARNING: Potentially hazardous agents detected" |
| "Your skin might not love this one"       | "This product is rated POOR"             |
| "Niacinamide — helps with dark spots and uneven texture" | "Niacinamide: B3 derivative, melanogenesis inhibitor" |
| "Scan another product"                    | "Return to scanner interface"            |

- Use sentence case for all UI text, including buttons and labels.
- Error messages explain what happened and what to do: "Barcode not found. Try entering it manually."
- Ingredient descriptions are one line, plain language. Save the science for an optional "Learn more" expansion.

---

## 9. Code Conventions

### File Structure

```
frontend/
├── src/
│   ├── components/          # Shared UI components
│   │   ├── ui/              # Primitives (Button, Input, Card, Badge)
│   │   └── product/         # Domain components (ScoreBar, IngredientList)
│   ├── pages/               # Route-level page components
│   ├── hooks/               # Custom React hooks
│   ├── lib/                 # Utilities, API client, scoring logic
│   ├── styles/              # Global CSS, Tailwind config
│   └── types/               # Shared TypeScript types
```

### Naming

- Components: `PascalCase.tsx` (e.g. `ScoreBar.tsx`, `ProductCard.tsx`).
- Hooks: `camelCase.ts` prefixed with `use` (e.g. `useBarcodeScan.ts`).
- Utilities: `camelCase.ts` (e.g. `calculateScore.ts`).
- Types: `PascalCase.ts` (e.g. `Product.ts`, `Ingredient.ts`).
- CSS classes: use Tailwind utilities. No custom CSS classes unless Tailwind can't express it.
- No barrel exports (`index.ts` re-exports). Import directly from the file.

### Tailwind Config

All design tokens above should live in `tailwind.config.ts` under `theme.extend`. Example:

```ts
// tailwind.config.ts
export default {
  theme: {
    extend: {
      colors: {
        ink:   { DEFAULT: '#09090B', light: '#18181B', muted: '#27272A' },
        rose:  { DEFAULT: '#DBAEBB', soft: '#F2E6EA', hover: '#D0A0AE', pressed: '#C48D9C' },
        sage:  { DEFAULT: '#8F9951', soft: '#EFF1E6', hover: '#7D8847', dark: '#5E6636' },
        stone: { DEFAULT: '#D6D6D1', light: '#F0F0ED', hover: '#C8C8C2', dark: '#A1A19B' },
        score: {
          excellent: '#5A7A2E',
          good: '#8F9951',
          fair: '#BFA24E',
          poor: '#BF7A3D',
          avoid: '#BF4040',
        },
      },
      fontFamily: {
        display: ['Stardom', 'serif'],
        sans:    ['Inter', 'system-ui', 'sans-serif'],
      },
      borderRadius: {
        sm:   '6px',
        md:   '12px',
        lg:   '16px',
        full: '9999px',
      },
      boxShadow: {
        sm: '0 1px 3px rgba(9, 9, 11, 0.06)',
        md: '0 4px 12px rgba(9, 9, 11, 0.08)',
      },
    },
  },
};
```

Then use `bg-rose`, `text-sage-dark`, `border-stone`, `bg-score-excellent` etc. throughout the codebase.

### General Rules

- TypeScript strict mode. No `any` — use `unknown` and narrow.
- Functional components only. No class components.
- State management: React hooks + context for now. No Redux unless complexity demands it.
- API calls: use a shared `api.ts` client wrapping `fetch`. No Axios.
- Error handling: every API call has loading, error, and empty states handled in the UI.
- Format with Prettier (default config). Lint with ESLint.
- Commit messages: conventional commits (`feat:`, `fix:`, `style:`, `refactor:`).

---

## 10. Accessibility

- Color contrast: all text meets WCAG 2.1 AA (4.5:1 for body, 3:1 for large text). Verify `rose` on white — at `#DBAEBB` it may fail for small text; use `rose-pressed` or `ink` for text on light backgrounds.
- Score meanings are never conveyed by color alone — always paired with a numeric score and a text label.
- Touch targets: `44px` minimum.
- Focus indicators: `2px` ring, `rose-soft` color, `2px` offset.
- Images: all product images have `alt` text (product name + brand).
- Screen reader: ingredient concern levels announced as text, not just dot colors.

---

## Quick Reference for AI Sessions

Paste this block at the top of any AI prompt for a condensed version:

```
Ingryd style tokens:
- Colors: ink #09090B, rose #DBAEBB, sage #8F9951, stone #D6D6D1
- Fonts: Stardom (display/headings only), Inter (everything else)
- Radius: 6/12/16px (sm/md/lg)
- Spacing base: 4px multiples
- Shadows: sm 0 1px 3px rgba(9,9,11,.06) / md 0 4px 12px rgba(9,9,11,.08)
- Buttons: 44px tall, 12px 24px padding, 12px radius, Inter 600
- Score colors: excellent #5A7A2E / good #8F9951 / fair #BFA24E / poor #BF7A3D / avoid #BF4040
- Tone: friendly, plain language, sentence case, no jargon
- Stack: React 18, TypeScript, Vite, Tailwind, FastAPI backend
- Icons: Lucide React, 20px, stroke 1.75, outline only
```
