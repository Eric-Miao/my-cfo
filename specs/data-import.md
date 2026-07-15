# Data Import

## Document Control

- Product: My CFO
- Scope: V1 strict CSV export/import for owner snapshot creation.
- Purpose: define CSV schema, validation, preview, commit, and failure handling.
- Requirement IDs: use `IMP-x.y` for stable cross-references.

## IMP-1 Import Scope

Supports: `PRD-6.1`, `PRD-6.5`, `API-6.8`, `API-10`, `SEC-8`.

### IMP-1.1 CSV Is Secondary

Manual web entry is the primary V1 workflow. CSV exists to speed up amount entry for app-defined balance-sheet templates.

### IMP-1.2 Template-Based Only

V1 imports only the CSV schema exported by the app. It does not parse bank, brokerage, payment app, or legacy spreadsheet formats.

### IMP-1.3 Draft Snapshots Only

CSV import creates draft owner snapshots only. It never creates confirmed owner snapshots, household groups, finalized group revisions, owners, templates, system categories, or tags.

## IMP-2 Export Contract

Supports: `PRD-6.2`, `API-6.8`, `SEC-8.3`.

### IMP-2.1 Export Source

CSV export uses currently active templates. Inactive templates are excluded.

### IMP-2.2 Export Columns

The exported CSV must include these columns in this order:

```text
template_id
owner_id
owner_name
item_type
system_category_id
system_category_code
system_category_name
account_name
institution_name
currency
tag_ids
tag_names
amount_original
note
```

### IMP-2.3 User-Editable Columns

Users may edit only:

```text
amount_original
note
```

All other columns are identity or validation fields and must remain unchanged for import.

### IMP-2.4 CSV Injection Mitigation

Export must escape or prefix user-controlled text cells that begin with formula-triggering characters such as `=`, `+`, `-`, or `@`.

## IMP-3 Import Request

Supports: `PRD-3.6`, `PRD-6.3`, `API-6.8`.

### IMP-3.1 File-Level Reporting Timestamp

`reporting_at` is supplied in the import request, not in each CSV row.

```json
{
  "reporting_at": "2026-03-31T15:59:59Z"
}
```

All draft owner snapshots created by the import use this timestamp.

### IMP-3.2 Multiple Owners

One CSV file may contain rows for multiple owners. Commit creates one draft owner snapshot per owner represented in valid rows.

### IMP-3.3 Authoritative Template Identity

`template_id` is the authoritative row identity. Human-readable columns are required for validation and user readability but do not identify the template by themselves.

## IMP-4 Validation Rules

Supports: `PRD-6.3`, `PRD-6.4`, `SEC-8.1`.

### IMP-4.1 Schema Validation

Import rejects files with missing columns, extra columns, reordered columns, duplicate headers, malformed CSV, or unsupported encodings.

### IMP-4.2 Template Match Validation

Each row must match the current active template referenced by `template_id`.

Import fails if any of these exported fields no longer match current template/master data:

- `owner_id`
- `owner_name`
- `item_type`
- `system_category_id`
- `system_category_code`
- `system_category_name`
- `account_name`
- `institution_name`
- `currency`
- `tag_ids`
- `tag_names`

If template configuration changed after export, the user must export a fresh CSV.

### IMP-4.3 Master Data Validation

Import rejects unknown or inactive:

- owners
- templates
- system categories
- tags

Import never creates missing master data.

### IMP-4.4 Amount Validation

`amount_original` is required for every imported row and must be a non-negative decimal string with up to 8 decimal places.

Valid examples:

```text
0
100
100.25
100.25000000
```

Invalid examples:

```text
-1
abc
100.123456789
```

### IMP-4.5 Note Validation

`note` is optional. Leading and trailing whitespace should be trimmed. Empty strings normalize to null.

## IMP-5 Preview Flow

Supports: `API-6.8`, `API-10`, `SEC-8.2`.

### IMP-5.1 Preview Endpoint

`POST /api/v1/csv/owner-snapshots/import/preview` validates the file and returns a preview result.

### IMP-5.2 Preview Response

Successful preview returns:

```json
{
  "valid": true,
  "preview_token": "preview_1",
  "reporting_at": "2026-03-31T15:59:59Z",
  "draft_snapshots": [
    {
      "owner_id": "owner_1",
      "owner_name": "龙龙",
      "item_count": 10
    }
  ],
  "errors": []
}
```

Failed preview returns `valid=false`, no commit-capable token, and row-level errors.

### IMP-5.3 Preview Token

Preview tokens are short-lived and bound to the authenticated admin session. A preview token can be used once.

## IMP-6 Commit Flow

Supports: `PRD-6.5`, `API-6.8`, `SEC-8.2`.

### IMP-6.1 Commit Endpoint

`POST /api/v1/csv/owner-snapshots/import/commit` creates draft owner snapshots from a valid preview token.

### IMP-6.2 Atomic Commit

Commit is atomic. Either all draft owner snapshots and snapshot items are created, or none are created.

### IMP-6.3 Duplicate Draft Handling

If an owner already has a draft snapshot with the same `reporting_at`, commit fails with a conflict. The user must cancel or complete the existing draft before importing again.

### IMP-6.4 Imported Snapshot Source

Created owner snapshots use:

```text
source = csv_import
status = draft
```

## IMP-7 Error Reporting

Supports: `API-4`, `API-10`.

Import errors use the standard API error shape and include row numbers where applicable.

Example:

```json
{
  "error": {
    "code": "import_error",
    "message": "CSV import failed validation.",
    "details": [
      {
        "row": 12,
        "field": "amount_original",
        "reason": "Amount must be non-negative."
      }
    ]
  }
}
```

Errors must not log full CSV contents or complete financial amounts by default.

## IMP-8 Traceability Matrix

| Requirement | Import Coverage |
|---|---|
| `PRD-3.6` | File-level `reporting_at` for imported snapshots |
| `PRD-6.1` | CSV as secondary workflow |
| `PRD-6.2` | Active-template export |
| `PRD-6.3` | Strict app-defined schema |
| `PRD-6.4` | Validation for references, currencies, amounts, and schema |
| `PRD-6.5` | Draft owner snapshots only |
| `API-6.8`, `API-10` | Preview/commit endpoints |
| `SEC-8.1` | Strict import |
| `SEC-8.2` | Preview before commit and no partial records |
| `SEC-8.3` | CSV injection mitigation on export |

## IMP-9 Verification Requirements

- Export tests must verify column order and active-template filtering.
- Export tests must verify formula-triggering user text is escaped or prefixed.
- Preview tests must reject changed template metadata.
- Preview tests must reject unknown or inactive owners, templates, categories, and tags.
- Preview tests must reject malformed, negative, and over-precision amounts.
- Commit tests must create one draft owner snapshot per owner in the CSV.
- Commit tests must prove no partial records are created on failure.
- Conflict tests must reject duplicate draft snapshots for the same owner and `reporting_at`.
