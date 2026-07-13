# Product Requirements

## Product Goal

V1 is a balance-sheet snapshot dashboard for personal/family finance. It helps a single admin user record point-in-time asset and liability snapshots for multiple owners, then review owner-level and household-level net worth trends over time.

V1 is not a bookkeeping, budgeting, cash-flow, or investment holding analysis system.

## Users

- Primary user: one admin user who can view and manage all data.
- Financial owners: people such as `猫猫` and `龙龙`. Owners are financial dimensions, not login identities.

## Core Workflow

1. Configure active owners.
2. Configure balance sheet item templates for each owner.
3. Create owner snapshots independently at any date.
4. Generate draft snapshot items from active templates.
5. Fill every amount; use `0` for checked zero balances.
6. Confirm owner snapshots.
7. Create a household snapshot group by selecting exactly one confirmed snapshot for every active owner.
8. Finalize the household snapshot group.
9. Review household and owner dashboards based on finalized data.

## Scope

### In Scope

- Owner management.
- Balance sheet item templates.
- Owner snapshots and snapshot items.
- Household snapshot groups.
- Household overview dashboard as the default homepage.
- Owner-level dashboard views.
- Snapshot-based time series charts.
- Multi-currency amounts with automatic FX rates and manual fallback.
- CSV template export and import based on app-defined templates.
- Single-user password login.
- SQLite storage.
- Lightweight revision history for finalized household groups.
- Notes and tags on templates and snapshot items.

### Out of Scope

- Transaction ledger.
- Cash-flow statement.
- Recurring commitments or fixed expense scheduling.
- Budgeting.
- Expense categorization.
- Holding-level investment breakdown.
- Automatic bank, payment app, or brokerage sync.
- Legacy spreadsheet parser.
- Owner-level login or permissions.
- Full audit log.
- CI/CD or deployment pipeline details.

## Data Model Requirements

### Owners

Owners are active financial subjects. A household snapshot group can be finalized only when every active owner has exactly one confirmed owner snapshot included.

### Balance Sheet Item Templates

Templates define the recurring rows expected in each owner snapshot:

- owner
- item type: asset or liability
- system category
- user category
- account name
- institution
- currency
- display order
- active status
- optional notes and tags

Templates are reused for future snapshots. Later template edits must not rewrite historical snapshot items.

### Snapshot Items

Snapshot items are generated from active templates. Draft items may be edited before confirmation. Confirmed owner snapshots cannot contain empty amounts.

Amount semantics:

- `0` means checked and confirmed as zero.
- Empty/null amount is allowed only while a snapshot is draft.
- Inactive templates are excluded from future snapshot generation but remain available in history.

### Snapshot Dates

Snapshots are point-in-time records. They may be created daily, weekly, monthly, or ad hoc. Monthly views are derived from snapshot dates and are not required by the data model.

### Household Snapshot Groups

A household snapshot group is a user-confirmed aggregation of one confirmed snapshot per active owner. Household dashboard totals and trends use finalized household snapshot groups only.

Finalized groups support lightweight revision history:

- Reopening a finalized group requires confirmation.
- Reopening creates an editable draft revision.
- The previous finalized revision remains active until a new revision is finalized.
- Saving edited draft data requires confirmation.
- Cancelling a draft revision leaves the previous finalized revision unchanged.

## Classification Requirements

Snapshot items use a two-level classification model:

- System category: stable calculation category used for totals and charts.
- User category: user-defined display/grouping category.

Calculation depends on item type, system category, currency, and amount. Display can use user category, account name, institution, notes, and tags.

## Currency Requirements

Base currency defaults to CNY. Snapshot items store original currency and original amount.

The system should fetch exchange rates automatically. If the FX source is unavailable, users can manually enter or override rates. Finalized household groups must freeze the FX rates used for base-currency calculations so historical totals do not drift.

## CSV Requirements

V1 supports manual web entry as the primary input method and CSV as a secondary workflow.

CSV template export:

- Export rows from active balance sheet item templates.
- Include owner, item type, system category, user category, account name, institution, and currency.
- Include blank amount and optional note fields for user input.

CSV import:

- Accept only the app-defined template schema.
- Reject unknown owners, invalid categories, invalid currencies, and malformed amounts.
- Preview parsed rows before saving.
- Create draft owner snapshots, not finalized household groups.

## Dashboard Requirements

The default homepage is Household Overview. It must display only active finalized household snapshot groups.

Required dashboard content:

- Current household net worth.
- Total assets.
- Total liabilities.
- Household net worth trend.
- Total assets vs total liabilities trend.
- Owner net worth trend.
- Asset composition by system category.
- Currency exposure.
- Owner contribution breakdown.
- Latest finalized group details.

Optional V1 dashboard content:

- Asset category trend.
- Currency exposure trend.
- Net worth delta between adjacent finalized groups.

Net worth delta may be shown, but it must be labeled as net worth change, not cash flow.

## Authentication & Storage Requirements

V1 uses single-user password login. One configured admin password protects dashboard and data-management pages. Owner records are financial dimensions, not login identities.

Secrets must come from environment variables and must not be committed. SQLite is the V1 source of truth. Spreadsheet and CSV files are import/export formats only.

## Acceptance Criteria

- Admin can configure active owners.
- Admin can configure active balance sheet item templates per owner.
- Admin can create draft owner snapshots from active templates.
- Admin cannot confirm an owner snapshot while any active template item has an empty amount.
- Admin can confirm owner snapshots with valid numeric amounts, including `0`.
- Admin can create and finalize a household snapshot group only when every active owner has exactly one confirmed snapshot selected.
- Household dashboard shows finalized groups only.
- Dashboard displays net worth, assets, liabilities, owner contribution, category composition, currency exposure, and required time series.
- System supports original-currency amounts and frozen FX rates for finalized household groups.
- Admin can export a CSV template from active templates.
- Admin can import the app-defined CSV format into draft owner snapshots after preview.
- Reopening a finalized group creates a draft revision and does not modify active dashboard totals until re-finalized.
- V1 does not require transaction import, expense categories, cash-flow analysis, holding-level investments, or bank/brokerage sync.
