# API Contract

## Document Control

- Product: My CFO
- Scope: V1 personal/family balance-sheet snapshot dashboard
- Purpose: define the REST API behavior that the frontend, backend tests, and Swagger/OpenAPI documentation must follow.
- Requirement IDs: use `API-x.y` for stable cross-references.

## API-1 Principles

Supports: `PRD-1.1`, `PRD-2.6`, `PRD-7.1`, `PRD-8.1`.

- Backend exposes REST APIs only; the frontend must not read the database or local files directly.
- All application endpoints use `/api/v1`.
- Swagger UI must be available at `/docs`; OpenAPI JSON must be available at `/openapi.json`.
- JSON is the only V1 request and response body format, except CSV import/export endpoints.
- Backend is the source of truth for validation, calculations, and snapshot finalization.
- Frontend consumes APIs through typed client modules generated from or checked against OpenAPI.

## API-2 Defaults and Data Formats

Supports: `PRD-5.1`, `PRD-5.3`, `PRD-5.7`.

- Timestamps use ISO-8601 strings with timezone, normalized to UTC in API responses.
- Dates and periods are derived from `reporting_at`; clients must not submit separate day, month, quarter, or year fields.
- Monetary amounts and FX rates are strings, never JSON numbers, to avoid floating-point precision loss.
- Decimal strings accept non-negative values with up to 8 decimal places, for example `"12345.67000000"`.
- Currency codes use uppercase ISO-style codes such as `CNY`, `USD`, `HKD`, and `JPY`.
- Resource IDs are opaque strings in API responses, even if the database stores integers internally.

## API-3 Authentication and Security

Supports: `PRD-8.1`, `PRD-8.2`.

- V1 uses one admin login identity.
- V1 has no registration endpoint, user table, role model, permission table, password reset, invitation flow, or owner-level access control.
- All authenticated requests have full admin access.
- Financial owners are data dimensions and are never authentication principals.
- Passwords and session/JWT secrets must come from environment variables only.
- Authentication uses FastAPI dependency-based protection on authenticated routers, not a global authentication middleware.
- Login returns an HttpOnly cookie session.
- All endpoints under `/api/v1` require authentication except `POST /api/v1/auth/login`.
- `GET /health`, `/docs`, and `/openapi.json` may remain unauthenticated for local development.
- V2 may migrate to database-backed users by bootstrapping the first admin user from the V1 environment-backed password hash.

## API-4 Response Envelope and Errors

All successful resource responses return the resource object directly. List responses return:

```json
{
  "items": [],
  "page": {
    "limit": 50,
    "next_cursor": null
  }
}
```

Errors use one consistent shape:

```json
{
  "error": {
    "code": "validation_error",
    "message": "One or more fields are invalid.",
    "details": [
      {
        "field": "amount_original",
        "reason": "Amount must be non-negative."
      }
    ]
  }
}
```

Default status codes:

- `400` for malformed requests or invalid state transitions.
- `401` for unauthenticated requests.
- `403` for authenticated requests that are not allowed.
- `404` for missing resources.
- `409` for stale edits, duplicate active records, or conflicting snapshot revisions.
- `422` for field-level validation errors.
- `500` for unexpected server errors.

## API-5 Pagination, Filtering, and Sorting

- List endpoints default to `limit=50` and cap `limit` at `200`.
- Cursor pagination is the default for mutable resources.
- `sort` accepts documented field names only, prefixed with `-` for descending order.
- Filter names match resource field names where practical, for example `owner_id`, `active`, `status`, and `reporting_at_from`.
- Invalid filters or sort fields return `422`.

## API-6 Endpoint Groups

### API-6.1 System

- `GET /health`: returns backend status for local and Compose health checks.

### API-6.2 Auth

- `POST /api/v1/auth/login`: authenticate the admin user.
- `POST /api/v1/auth/logout`: end the current session.
- `GET /api/v1/auth/me`: return the current admin identity.

### API-6.3 Master Data

- `GET /api/v1/owners`
- `POST /api/v1/owners`
- `PATCH /api/v1/owners/{owner_id}`
- `POST /api/v1/owners/{owner_id}/deactivate`
- `POST /api/v1/owners/{owner_id}/recover`
- `GET /api/v1/system-categories`
- `POST /api/v1/system-categories`
- `PATCH /api/v1/system-categories/{category_id}`
- `GET /api/v1/tags`
- `POST /api/v1/tags`
- `PATCH /api/v1/tags/{tag_id}`
- `GET /api/v1/templates`
- `POST /api/v1/templates`
- `PATCH /api/v1/templates/{template_id}`
- `POST /api/v1/templates/{template_id}/deactivate`
- `POST /api/v1/templates/{template_id}/recover`
- `GET /api/v1/institution-suggestions?query={text}`

Institution suggestions are derived from existing template and snapshot item text. Institution is not a V1 entity.

### API-6.4 Owner Snapshots

- `POST /api/v1/owner-snapshots`: create a draft snapshot from active templates.
- `GET /api/v1/owner-snapshots`
- `GET /api/v1/owner-snapshots/{snapshot_id}`
- `PATCH /api/v1/owner-snapshots/{snapshot_id}`: edit draft metadata only.
- `PATCH /api/v1/owner-snapshots/{snapshot_id}/items/{item_id}`: edit draft item amount and note.
- `POST /api/v1/owner-snapshots/{snapshot_id}/confirm`: confirm a complete draft.
- `POST /api/v1/owner-snapshots/{snapshot_id}/cancel`: cancel a draft.
- `POST /api/v1/owner-snapshots/{snapshot_id}/replacements`: create a draft replacement for a confirmed snapshot.

Confirmed snapshots are immutable. Corrections must use replacement endpoints.

### API-6.5 Household Groups

- `POST /api/v1/snapshot-groups`: create a group with one confirmed snapshot per active owner.
- `GET /api/v1/snapshot-groups`
- `GET /api/v1/snapshot-groups/{group_id}`
- `PATCH /api/v1/snapshot-groups/{group_id}/draft-revision`: update draft member selection or note.
- `POST /api/v1/snapshot-groups/{group_id}/finalize`: freeze selected owner snapshots and FX rate set.
- `POST /api/v1/snapshot-groups/{group_id}/reopen`: create a draft revision.
- `POST /api/v1/snapshot-groups/{group_id}/cancel-draft`: cancel the current draft revision.

Finalized revisions are never edited in place.

### API-6.6 FX Rates

- `POST /api/v1/fx-rates/quote`: preview API-backed rates for selected currencies.
- `GET /api/v1/fx-rate-sets/{fx_rate_set_id}`: read a frozen FX rate set.

FX quotes are previews. Official FX rate sets are created only when a household group revision is finalized.

### API-6.7 Dashboard

- `GET /api/v1/dashboard/household-overview`: latest finalized household overview.
- `GET /api/v1/dashboard/net-worth-trend`
- `GET /api/v1/dashboard/assets-liabilities-trend`
- `GET /api/v1/dashboard/owner-net-worth-trend`
- `GET /api/v1/dashboard/composition`
- `GET /api/v1/dashboard/latest-group-detail`

Dashboard endpoints read finalized household group revisions only for official values.

Dashboard endpoints may accept `display_currency`. If it differs from the official base currency, returned display values must be marked as estimates.

### API-6.8 CSV Import and Export

- `GET /api/v1/csv/templates/export`: export active templates.
- `POST /api/v1/csv/owner-snapshots/import/preview`: validate CSV and return a preview token.
- `POST /api/v1/csv/owner-snapshots/import/commit`: create draft owner snapshots from a valid preview token.

CSV import never creates finalized household groups or master data.

## API-7 Resource Schemas

### API-7.1 Owner

Supports: `PRD-1.3`, `PRD-3.1`.

```json
{
  "id": "owner_1",
  "name": "龙龙",
  "display_order": 10,
  "active": true,
  "created_at": "2026-07-13T02:00:00Z",
  "updated_at": "2026-07-13T02:00:00Z"
}
```

### API-7.2 System Category

Supports: `PRD-4.1`, `PRD-7.4`.

```json
{
  "id": "cat_1",
  "item_type": "asset",
  "code": "bank_deposit",
  "name": "Bank Deposit",
  "calculation_role": "asset_total",
  "display_order": 10,
  "active": true
}
```

### API-7.3 Tag

Supports: `PRD-4.2`, `PRD-7.6`.

```json
{
  "id": "tag_1",
  "name": "long term",
  "normalized_name": "long term",
  "color": "#3366cc",
  "description": "Long-term holdings",
  "active": true
}
```

### API-7.4 Template

Supports: `PRD-3.2`, `PRD-3.3`, `PRD-3.4`, `PRD-3.5`.

```json
{
  "id": "tpl_1",
  "owner_id": "owner_1",
  "item_type": "asset",
  "system_category_id": "cat_1",
  "account_name": "Fidelity Brokerage",
  "institution_name": "Fidelity",
  "currency": "USD",
  "display_order": 10,
  "active": true,
  "note": "Main brokerage reporting line",
  "tags": [
    {
      "id": "tag_1",
      "name": "long term"
    }
  ]
}
```

Template updates change future generated snapshot items only. Existing snapshot items keep copied historical values.

### API-7.5 Owner Snapshot

Supports: `PRD-2.2`, `PRD-2.3`, `PRD-3.6`, `PRD-3.7`, `PRD-3.8`.

```json
{
  "id": "snap_1",
  "owner_id": "owner_1",
  "reporting_at": "2026-03-31T15:59:59Z",
  "status": "draft",
  "source": "manual",
  "label": "March 2026",
  "replaces_snapshot_id": null,
  "superseded_by_snapshot_id": null,
  "items": [
    {
      "id": "item_1",
      "template_id": "tpl_1",
      "item_type": "asset",
      "system_category_id": "cat_1",
      "system_category_code_snapshot": "bank_deposit",
      "system_category_name_snapshot": "Bank Deposit",
      "account_name_snapshot": "Fidelity Brokerage",
      "institution_name_snapshot": "Fidelity",
      "currency": "USD",
      "amount_original": null,
      "note": null,
      "display_order": 10,
      "tags": [
        {
          "tag_id": "tag_1",
          "tag_name_snapshot": "long term"
        }
      ]
    }
  ]
}
```

Snapshot item updates accept `amount_original`, `currency`, and `note` only while the owner snapshot is `draft`.

### API-7.6 Household Group Revision

Supports: `PRD-2.4`, `PRD-2.5`, `PRD-3.9`, `PRD-3.10`, `PRD-3.11`, `PRD-5.4`.

```json
{
  "id": "rev_1",
  "snapshot_group_id": "group_1",
  "revision_number": 1,
  "status": "draft",
  "base_currency": "CNY",
  "fx_rate_set_id": null,
  "members": [
    {
      "owner_id": "owner_1",
      "owner_snapshot_id": "snap_1",
      "owner_snapshot_reporting_at": "2026-03-31T15:59:59Z"
    }
  ],
  "note": null
}
```

Finalization creates or attaches the frozen FX rate set and changes the revision to `finalized`.

### API-7.7 Dashboard Household Overview

Supports: `PRD-2.6`, `PRD-5.6`, `PRD-7.1`, `PRD-7.2`, `PRD-7.3`, `PRD-7.4`, `PRD-7.5`.

```json
{
  "official_base_currency": "CNY",
  "display_currency": "USD",
  "display_values_are_estimates": true,
  "current": {
    "group_id": "group_1",
    "revision_id": "rev_1",
    "reporting_at": "2026-07-13T02:00:00Z",
    "net_worth_official": "1000000.00000000",
    "total_assets_official": "1200000.00000000",
    "total_liabilities_official": "200000.00000000",
    "net_worth_display": "137931.03000000"
  },
  "trends": {
    "net_worth": [],
    "assets_vs_liabilities": [],
    "owner_net_worth": []
  },
  "composition": {
    "system_categories": [],
    "currency_exposure": [],
    "owner_contribution": []
  },
  "latest_group_detail": {
    "members": []
  }
}
```

## API-8 Write Request Contracts

### API-8.1 Create Owner Snapshot

```json
{
  "owner_id": "owner_1",
  "reporting_at": "2026-03-31T15:59:59Z",
  "label": "March 2026",
  "source": "manual"
}
```

The server generates items from active templates for the owner.

### API-8.2 Update Snapshot Item

```json
{
  "amount_original": "10000.00000000",
  "currency": "USD",
  "note": "Checked against statement"
}
```

`amount_original` must be null for draft incomplete values or a non-negative decimal string. Confirmed snapshots reject updates.

### API-8.3 Create Household Group

```json
{
  "label": "Household March 2026",
  "members": [
    {
      "owner_id": "owner_1",
      "owner_snapshot_id": "snap_1"
    }
  ]
}
```

The server generates group `reporting_at`.

### API-8.4 Finalize Household Group

API-backed FX:

```json
{
  "fx_rates": {
    "mode": "api"
  }
}
```

Manual fallback:

```json
{
  "fx_rates": {
    "mode": "manual",
    "manual_rates": [
      {
        "currency": "USD",
        "rate_to_base": "7.25000000"
      }
    ]
  }
}
```

## API-9 State Transition Rules

Supports: `PRD-3.7`, `PRD-3.8`, `PRD-3.11`, `PRD-8.4`.

Owner snapshot states:

```text
draft -> confirmed
draft -> cancelled
confirmed -> superseded    # only when replacement confirms
```

Snapshot group revision states:

```text
draft -> finalized
draft -> cancelled
finalized -> superseded    # only when a newer revision finalizes
```

Invalid transitions return `409`.

## API-10 CSV Contracts

Supports: `PRD-6.1`, `PRD-6.2`, `PRD-6.3`, `PRD-6.4`, `PRD-6.5`.

CSV export returns a file generated from active templates. CSV import is two-phase:

1. Preview validates schema, master-data references, currencies, tags, amount format, and negative amounts.
2. Commit creates draft owner snapshots from a valid preview token.

Preview response:

```json
{
  "valid": true,
  "preview_token": "preview_1",
  "draft_snapshots": [
    {
      "owner_id": "owner_1",
      "reporting_at": "2026-03-31T15:59:59Z",
      "item_count": 10
    }
  ],
  "errors": []
}
```

Import errors use `IMPORT_ERROR` details and never create partial records.

## API-11 Traceability Matrix

| PRD ID | API Coverage |
|---|---|
| `PRD-1.2`, `PRD-8.1`, `PRD-8.2` | Authentication and security conventions |
| `PRD-2.1`, `PRD-3.1`, `PRD-4.1`, `PRD-4.2`, `PRD-4.4` | Master data endpoints |
| `PRD-2.2`, `PRD-2.3`, `PRD-3.6`, `PRD-3.7`, `PRD-3.8` | Owner snapshot endpoints and schemas |
| `PRD-2.4`, `PRD-2.5`, `PRD-3.9`, `PRD-3.10`, `PRD-3.11` | Household group endpoints and schemas |
| `PRD-5.1`, `PRD-5.2`, `PRD-5.7` | Snapshot item validation and decimal formats |
| `PRD-5.3`, `PRD-5.4`, `PRD-5.5`, `PRD-5.6` | FX and dashboard estimate behavior |
| `PRD-6.1` through `PRD-6.5` | CSV endpoints |
| `PRD-7.1` through `PRD-7.6` | Dashboard endpoints |
| `PRD-8.3`, `PRD-8.4` | Persistence-backed lifecycle behavior |

## API-12 OpenAPI and Tests

- Every endpoint must appear in OpenAPI before frontend integration.
- Backend tests must exercise REST API behavior through HTTP clients, not direct service calls only.
- State-transition endpoints must test allowed transitions and rejected transitions.
- Dashboard API tests must verify that official values come only from finalized household group revisions.
