# Dashboard UI Design

## Document Control

- Product: My CFO
- Scope: V1 dashboard interface, themes, layout, components, and bilingual behavior.
- Purpose: define UI decisions separately from dashboard data behavior.
- Requirement IDs: use `DUI-x.y` for stable cross-references.

## DUI-1 UI Direction

Supports: `PRD-7.1`, `PRD-7.2`, `PRD-7.3`, `PRD-7.4`.

The dashboard should feel like a focused financial control panel: dense enough for real data review, calm enough for personal finance. It may reference the provided trading-platform design language, but it must not copy brand marks, proprietary fonts, copy, or trading-specific affordances.

Adopt these translated principles:

- dark financial dashboard as the default experience
- one strong yellow accent for primary actions and important highlights
- green/red only for directional financial deltas, not generic success/error
- flat cards with clear surface contrast instead of heavy shadows
- compact data tables and charts
- financial numbers rendered with tabular numerals

## DUI-2 Theme System

### DUI-2.1 Theme Modes

The UI supports light and dark themes.

- Dark theme is the default for dashboard views.
- Light theme is available through a persistent user toggle.
- Theme selection may be stored in local UI preference storage because it is not sensitive financial data.

### DUI-2.2 Color Tokens

```text
color.canvas.dark = #0b0e11
color.surface.dark = #1e2329
color.surface.elevated_dark = #2b3139
color.canvas.light = #ffffff
color.surface.light = #fafafa
color.border.light = #eaecef
color.border.dark = #2b3139
color.text.primary_dark = #eaecef
color.text.primary_light = #181a20
color.text.muted = #707a8a
color.accent.primary = #FCD535
color.accent.primary_active = #f0b90b
color.delta.positive = #0ecb81
color.delta.negative = #f6465d
color.info = #3b82f6
```

Yellow is reserved for:

- primary actions
- active nav state
- key financial highlight
- selected filter state

Do not use yellow for body text or large decorative fills.

## DUI-3 Language System

Supports: `PRD-1.2`.

### DUI-3.1 Supported Languages

V1 supports English and Simplified Chinese:

```text
en-US
zh-CN
```

### DUI-3.2 Language Toggle

A language toggle appears in the top navigation. The selected language persists as a UI preference.

### DUI-3.3 Copy Requirements

All navigation labels, metric labels, empty states, form labels, table headers, filter labels, and error summaries must use translation keys. Hardcoded user-facing copy is not allowed in Vue components.

Financial owner names, account names, institution names, tags, notes, and imported data remain user-provided content and are not translated.

## DUI-4 Typography

Use system fonts by default:

```text
font.sans = Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif
font.number = "IBM Plex Sans", "JetBrains Mono", ui-monospace, SFMono-Regular, monospace
```

Number-heavy values must use `font.number` or CSS tabular numerals:

```css
font-variant-numeric: tabular-nums;
```

Type scale:

| Token | Size | Weight | Use |
|---|---:|---:|---|
| `text.display` | 40px | 700 | current net worth |
| `text.title_lg` | 24px | 600 | page title |
| `text.title_md` | 20px | 600 | card title |
| `text.body` | 14px | 400 | default text |
| `text.caption` | 12px | 500 | labels and metadata |
| `text.number` | 16px | 500 | table and chart values |

## DUI-5 Layout

### DUI-5.1 App Shell

Dashboard pages use:

- top navigation with product name, primary nav, theme toggle, language toggle, and logout
- main content container max width `1440px`
- responsive grid with 24px desktop gutters and 16px mobile gutters

### DUI-5.2 Household Overview Layout

Desktop order:

1. top summary row: net worth, total assets, total liabilities, latest group timestamp
2. main trend card: household net worth trend
3. side cards: owner contribution and currency exposure
4. assets versus liabilities chart
5. system category composition
6. latest finalized group detail table

Mobile order:

1. net worth summary
2. assets/liabilities summary
3. net worth trend
4. owner contribution
5. composition cards
6. latest group detail

### DUI-5.3 Owner Dashboard Layout

Owner dashboard uses the same shell with owner selector, owner summary cards, owner trend, owner category composition, currency exposure, and latest selected owner snapshot detail.

## DUI-6 Components

### DUI-6.1 Metric Card

Metric cards show label, value, optional delta, official/estimate badge, and timestamp. Values use tabular numbers. Estimate badges are required when display currency differs from official base currency.

### DUI-6.2 Chart Card

Chart cards contain title, subtitle, filter summary, chart area, and compact legend. ECharts is the V1 charting library.

Chart defaults:

- line chart for net worth trend
- stacked or grouped line/bar for assets vs liabilities
- donut or horizontal bar for composition
- horizontal bar for owner contribution
- table-plus-bar for currency exposure

### DUI-6.3 Latest Group Detail Table

The table shows owner, owner snapshot timestamp, account/reporting line, item type, system category, original amount, original currency, official base value, tags, and note.

Tables should support horizontal scroll on mobile.

### DUI-6.4 Filter Bar

The filter bar supports date range, display currency, owner, system category, and tag filters. Filters should be visible but compact; avoid modal-heavy flows for common dashboard filtering.

### DUI-6.5 Empty State

Empty states use one short explanation and one primary action. Example:

```text
No finalized household snapshot yet.
Finalize a household group to unlock dashboard trends.
```

## DUI-7 Interaction Rules

- Avoid complex animation.
- Chart transitions may be subtle and under 200ms.
- Theme and language switches should not reload the page.
- Dashboard filters update data through API calls and show loading states.
- State-changing dashboard actions should route to the relevant management page rather than mutate data inline.

## DUI-8 Responsive Behavior

| Breakpoint | Width | Behavior |
|---|---:|---|
| Mobile | `<768px` | nav collapses, cards stack, tables scroll horizontally |
| Tablet | `768-1024px` | two-column cards, compact filters |
| Desktop | `1024-1440px` | full dashboard grid |
| Wide | `>1440px` | centered max-width container |

Touch targets should be at least 40px high, with 44px effective target spacing where practical.

## DUI-9 Accessibility

- Text contrast must meet WCAG AA.
- Theme toggle and language toggle must be keyboard accessible.
- Charts need textual summaries or accessible table equivalents.
- Do not rely on color alone for positive/negative deltas.
- Focus rings must be visible in both themes.

## DUI-10 Traceability Matrix

| Requirement | UI Coverage |
|---|---|
| `PRD-7.1` | household overview as default homepage |
| `PRD-7.2` | summary metric cards |
| `PRD-7.3` | required trend chart cards |
| `PRD-7.4` | composition, currency exposure, owner contribution views |
| `PRD-7.5` | latest group detail table |
| `PRD-7.6` | optional tag drilldowns and net worth delta |
| `DASH-1.2` | official/estimate badge behavior |
| `API-6.7` | dashboard endpoint consumption |

## DUI-11 Verification Requirements

- UI tests must verify language toggle changes labels without changing user-provided financial data.
- UI tests must verify theme toggle applies dark and light tokens.
- UI tests must verify estimate badges appear when display currency differs from official base currency.
- UI tests must verify mobile tables remain usable with horizontal scroll.
- Accessibility checks must verify keyboard access to filters, toggles, and nav.
