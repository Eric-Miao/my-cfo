# Dashboard Design

## Document Control

- Product: My CFO
- Scope: V1 dashboard data behavior, view model, filters, and API alignment.
- Purpose: define non-UI dashboard requirements separately from visual design.
- Requirement IDs: use `DASH-x.y` for stable cross-references.

## DASH-1 Dashboard Principles

Supports: `PRD-2.6`, `PRD-7.1`, `API-6.7`.

### DASH-1.1 Official Data Source

Official dashboard values come only from finalized household group revisions. Draft, cancelled, superseded, and ungrouped owner snapshots are excluded from official dashboard totals and trends.

### DASH-1.2 Official vs Estimate

Official values use the frozen FX rate set attached to each finalized group revision. If a user selects a display currency different from the official base currency, converted values are presentation-only estimates and must be marked as estimates.

### DASH-1.3 No Cash-Flow Language

The dashboard must not label net worth changes as cash flow, income, expense, profit, or loss. Adjacent changes are labeled as net worth change or delta.

## DASH-2 Views

### DASH-2.1 Household Overview

Supports: `PRD-7.1`, `PRD-7.2`, `PRD-7.3`, `PRD-7.4`, `PRD-7.5`.

The default homepage is Household Overview. It shows the latest finalized household group and historical finalized group trends.

Required content:

- current household net worth
- total assets
- total liabilities
- household net worth trend
- total assets versus total liabilities trend
- owner net worth trend
- asset and liability composition by system category
- currency exposure
- owner contribution breakdown
- latest finalized group details

### DASH-2.2 Owner Dashboard

Supports: `PRD-2.6`, `PRD-7.3`, `PRD-7.5`.

Owner dashboards are derived from finalized household groups that include the selected owner. They do not use standalone confirmed owner snapshots unless those snapshots are selected by finalized group revisions.

Required content:

- selected owner current net worth
- selected owner assets and liabilities
- selected owner trend
- selected owner system category composition
- selected owner currency exposure
- latest finalized owner snapshot detail within household group context

### DASH-2.3 Latest Group Detail

Supports: `PRD-7.5`, `API-7.6`.

Latest group detail shows:

- household group ID and revision ID
- group `reporting_at`
- finalized timestamp
- official base currency
- frozen FX rate set summary
- selected owner snapshots and their individual `reporting_at` values
- item-level detail grouped by owner, item type, system category, currency, and tag

## DASH-3 Metrics and Calculations

Supports: `PRD-5.1`, `PRD-5.2`, `PRD-5.4`, `PRD-5.6`, `PRD-5.7`.

### DASH-3.1 Asset and Liability Totals

Asset totals sum snapshot items where `item_type=asset`. Liability totals sum snapshot items where `item_type=liability`. Amounts are converted from original currency to official base currency using the finalized group revision FX rate set.

### DASH-3.2 Net Worth

```text
net_worth = total_assets - total_liabilities
```

Amounts are decimal strings in API responses and must be formatted in the frontend according to currency display rules.

### DASH-3.3 Owner Contribution

Owner contribution is each owner net worth divided by household net worth for the same finalized group revision. If household net worth is zero or negative, show contribution as an absolute amount and suppress percentage share.

### DASH-3.4 Currency Exposure

Currency exposure groups original snapshot item amounts by original currency, then reports official base-currency equivalent using the group revision FX rate set.

### DASH-3.5 Tag Drilldown

Tag filtering includes all finalized snapshot items carrying the selected tag ID. Historical tag display uses `tag_name_snapshot`; continuity uses `tag_id`.

## DASH-4 Filters and Parameters

Supports: `API-6.7`, `API-7.7`.

Dashboard endpoints support:

- `from`: optional ISO timestamp
- `to`: optional ISO timestamp
- `display_currency`: optional estimate currency
- `owner_id`: owner dashboard or owner filter
- `system_category_id`: composition drilldown
- `tag_id`: tag drilldown

Invalid filters return API validation errors.

## DASH-5 Empty and Edge States

### DASH-5.1 No Finalized Groups

Show an empty state explaining that dashboards require finalized household groups. Primary action: create or finalize a household group.

### DASH-5.2 Missing FX Rate

Finalized groups should not exist without required frozen FX rates. If legacy or corrupted data lacks rates, show an error state and exclude the group from official charts until repaired.

### DASH-5.3 Negative Net Worth

Negative net worth is valid. Use clear liability-oriented copy and do not treat it as an application error.

### DASH-5.4 Mixed Owner Snapshot Dates

Owner snapshots inside a group may have different `reporting_at` values. Latest group detail must show each selected owner snapshot timestamp.

## DASH-6 API Mapping

| Dashboard Need | API |
|---|---|
| Household overview | `GET /api/v1/dashboard/household-overview` |
| Net worth trend | `GET /api/v1/dashboard/net-worth-trend` |
| Assets vs liabilities | `GET /api/v1/dashboard/assets-liabilities-trend` |
| Owner trend | `GET /api/v1/dashboard/owner-net-worth-trend` |
| Composition and exposure | `GET /api/v1/dashboard/composition` |
| Latest group detail | `GET /api/v1/dashboard/latest-group-detail` |

## DASH-7 Traceability Matrix

| Requirement | Dashboard Coverage |
|---|---|
| `PRD-2.6` | finalized household group revisions only |
| `PRD-5.1` through `PRD-5.7` | original currency, official FX, decimal handling, display estimates |
| `PRD-7.1` | household overview default |
| `PRD-7.2` | summary metrics |
| `PRD-7.3` | trend charts |
| `PRD-7.4` | composition views |
| `PRD-7.5` | latest group detail |
| `PRD-7.6` | optional drilldowns and net worth delta |
| `API-6.7`, `API-7.7` | dashboard endpoints and response contract |

## DASH-8 Verification Requirements

- Tests must prove draft, cancelled, superseded, and ungrouped snapshots are excluded from official dashboard values.
- Tests must prove official values use frozen FX rates from finalized group revisions.
- Tests must prove display-currency values are marked as estimates when different from official base currency.
- Tests must prove owner dashboards use finalized group membership, not standalone snapshots.
- Tests must prove net worth delta is not labeled as cash flow.
