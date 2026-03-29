#!/bin/sh
set -eu

validate_db_name() {
    case "$1" in
        *[!A-Za-z0-9_]* | "")
            echo "Invalid database name: $1" >&2
            exit 1
            ;;
    esac
}

create_db_if_missing() {
    db_name="$1"
    validate_db_name "$db_name"

    exists="$(
        psql \
            -h "$DB_HOST" \
            -U "$POSTGRES_USER" \
            -d "$POSTGRES_DB" \
            -tAc "SELECT 1 FROM pg_database WHERE datname = '$db_name'"
    )"

    if [ "$exists" = "1" ]; then
        echo "Database already exists: $db_name"
        return
    fi

    echo "Creating database: $db_name"
    createdb -h "$DB_HOST" -U "$POSTGRES_USER" "$db_name"
}

create_db_if_missing "$CARGO_DB_NAME"
create_db_if_missing "$LOCATION_DB_NAME"
create_db_if_missing "$INVENTORY_DB_NAME"
create_db_if_missing "$SUPPLIER_DB_NAME"
create_db_if_missing "$STAFF_DB_NAME"
create_db_if_missing "$EQUIPMENT_DB_NAME"
