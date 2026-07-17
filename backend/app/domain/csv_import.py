import csv
import io

TEMPLATE_EXPORT_COLUMNS = [
    "template_id",
    "owner_id",
    "owner_name",
    "item_type",
    "system_category_id",
    "system_category_code",
    "system_category_name",
    "account_name",
    "institution_name",
    "currency",
    "tag_ids",
    "tag_names",
    "amount_original",
    "note",
]

FORMULA_TRIGGER_PREFIXES = ("=", "+", "-", "@")


def escape_csv_text(value: str | None) -> str:
    if value is None:
        return ""
    if value.startswith(FORMULA_TRIGGER_PREFIXES):
        return f"'{value}"
    return value


def render_template_csv(rows: list[dict[str, str]]) -> str:
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=TEMPLATE_EXPORT_COLUMNS)
    writer.writeheader()
    for row in rows:
        writer.writerow(row)
    return output.getvalue()
