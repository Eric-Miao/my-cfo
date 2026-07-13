# Product Requirements Document

## Document Control

- Product: My CFO
- Scope: V1 personal/family balance-sheet snapshot dashboard
- Purpose: define traceable product requirements for design, data model, implementation, and tests.
- Requirement IDs: use `PRD-x.y` for stable cross-references.

## PRD-1 Product Scope

### PRD-1.1 Product Objective

The product shall help one admin user record point-in-time assets and liabilities for multiple financial owners, combine selected owner snapshots into finalized household snapshots, and review household and owner-level net worth trends.

### PRD-1.2 Primary User

The product shall support one admin login identity with access to all configuration, import/export, snapshot finalization, and dashboard functions.

### PRD-1.3 Financial Owners

The product shall support multiple financial owners, such as `猫猫` and `龙龙`, as ownership dimensions rather than login identities.

### PRD-1.4 V1 Non-Goals

V1 shall not include transaction ledgers, cash-flow statements, budgeting, expense categorization, holding-level investment analysis, automatic bank/brokerage sync, multi-user permissions, full audit logging, CI/CD pipeline design, or legacy spreadsheet parsing.

## PRD-2 Core Workflow

### PRD-2.1 Master Data Setup

The admin shall configure owners, controlled system categories, managed tags, and balance-sheet item templates before creating snapshots.

### PRD-2.2 Owner Snapshot Creation

The admin shall create draft owner snapshots from active templates and fill generated snapshot item amounts.

### PRD-2.3 Owner Snapshot Confirmation

The product shall prevent owner snapshot confirmation while any generated item has an empty amount. A value of `0` shall mean the balance was checked and confirmed as zero.

### PRD-2.4 Household Group Creation

The admin shall create a household snapshot group by explicitly selecting one confirmed owner snapshot for every owner active at finalization time.

### PRD-2.5 Household Group Finalization

The product shall finalize household groups by freezing selected owner snapshots and the FX rate set used for official base-currency totals.

### PRD-2.6 Dashboard Review

The product shall render household and owner dashboards from finalized household group revisions only for official values.

## PRD-3 Data and Snapshot Requirements

### PRD-3.1 Owner Lifecycle

The admin shall be able to create, rename, activate, deactivate, and recover owners. Historical snapshots and finalized groups shall retain their original owner references.

### PRD-3.2 Template Semantics

A balance-sheet item template shall represent one recurring reporting line, not a full account, sub-account, or investment holding model.

### PRD-3.3 Template Fields

Templates shall include owner, item type, controlled system category, account name, institution name, currency, display order, active status, notes, and tags.

### PRD-3.4 Template Change Scope

Template edits shall affect future generated snapshot items only. Existing snapshot items shall preserve copied historical fields.

### PRD-3.5 Template Active State

Inactive templates shall stop generating future snapshot items but remain available for historical records and recovery.

### PRD-3.6 Owner Snapshot Timestamp

Owner snapshots shall use a canonical `reporting_at` timestamp. Day, month, quarter, and year views shall be derived from that timestamp.

### PRD-3.7 Confirmed Snapshot Immutability

Confirmed owner snapshots shall not be edited in place.

### PRD-3.8 Replacement Snapshot Corrections

Corrections to confirmed owner snapshots shall create replacement snapshots. Confirming a replacement shall mark the previous snapshot as superseded and link both records.

### PRD-3.9 Household Group Timestamp

Household snapshot group `reporting_at` shall be generated automatically when the group is created and shall not be manually selected in V1.

### PRD-3.10 Household Group Derivation

Household group revisions shall be derived from selected owner snapshots and shall not directly own or edit financial amounts.

### PRD-3.11 Household Group Revision

Reopening a finalized household group shall create a draft revision. The previous finalized revision shall remain active until a new revision is finalized.

## PRD-4 Classification and Labeling

### PRD-4.1 Controlled System Categories

System categories shall be controlled, user-configurable dashboard categories with item-type compatibility.

### PRD-4.2 Managed Tags

Tags shall be managed entities used for filtering, drilldown, and auxiliary labeling.

### PRD-4.3 No User Category Field

V1 shall not use a separate `user_category` field. The product shall use controlled system categories and managed tags instead.

### PRD-4.4 Institution Label

Institution shall be a normalized text label with autocomplete from existing values, not an independent V1 entity.

## PRD-5 Currency and Valuation

### PRD-5.1 Original Currency Storage

Snapshot items shall store original amount and original currency.

### PRD-5.2 Non-Negative Amounts

Snapshot item amounts shall be non-negative. Item type shall determine whether a value contributes to assets or liabilities.

### PRD-5.3 Official Base Currency

V1 shall use one global official base currency, defaulting to CNY.

### PRD-5.4 Frozen FX Rates

Finalized household group revisions shall freeze the FX rate set used for official base-currency totals.

### PRD-5.5 FX Source and Fallback

The product shall fetch FX rates from an API when available and support manual fallback when the API is unavailable or insufficient.

### PRD-5.6 Display Currency Estimates

Dashboard display-currency conversions shall be presentation-only estimates when they differ from frozen official base-currency values and shall not mutate historical records.

### PRD-5.7 Decimal Precision

Amounts and FX rates shall be stored without floating-point precision loss and shall support up to 8 decimal places.

## PRD-6 CSV Import and Export

### PRD-6.1 CSV Role

CSV shall be a secondary workflow. Manual web entry shall remain the primary workflow.

### PRD-6.2 CSV Export

CSV exports shall be generated from active templates.

### PRD-6.3 Strict CSV Import

CSV imports shall strictly follow the app-defined exported template schema.

### PRD-6.4 CSV Validation

CSV import shall reject unknown owners, unknown templates, unknown system categories, unknown tags, invalid currencies, malformed amounts, and negative amounts.

### PRD-6.5 CSV Import Output

CSV import shall create draft owner snapshots only and shall never create finalized household groups or master data.

## PRD-7 Dashboard Requirements

### PRD-7.1 Default Dashboard

The default homepage shall be Household Overview and shall use finalized household group revisions only.

### PRD-7.2 Required Summary Metrics

The dashboard shall show current household net worth, total assets, and total liabilities.

### PRD-7.3 Required Trend Charts

The dashboard shall show household net worth trend, total assets versus liabilities trend, and owner net worth trend.

### PRD-7.4 Required Composition Views

The dashboard shall show asset and liability composition by system category, currency exposure, and owner contribution breakdown.

### PRD-7.5 Latest Group Detail

The dashboard shall show latest finalized group details, including selected owner snapshot timestamps.

### PRD-7.6 Optional V1 Views

V1 may include system category trends, currency exposure trends, tag filters, tag drilldowns, and adjacent net worth delta. Net worth delta shall be labeled as net worth change, not cash flow.

## PRD-8 Security and Storage

### PRD-8.1 Authentication

V1 shall use single-user password login.

### PRD-8.2 Secret Handling

Passwords, tokens, secrets, connection strings, and private keys shall come from environment variables and shall not be committed.

### PRD-8.3 Source of Truth

SQLite shall be the V1 source of truth. Spreadsheet and CSV files shall be import/export formats only.

### PRD-8.4 Soft Delete and Recovery

Referenced records shall not be hard-deleted. The product shall use active flags or status fields to support deactivation, cancellation, supersession, and recovery.
