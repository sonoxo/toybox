#!/usr/bin/env python3
"""Validate Toybox ontology schema and optional generated catalog data."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def fail(message: str) -> None:
    raise ValueError(message)


def load(path: str) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def validate_schema(schema: dict) -> None:
    for key in ("ontology", "objectTypes", "linkTypes", "actionTypes"):
        if key not in schema:
            fail(f"schema missing required key: {key}")

    object_types = schema["objectTypes"]
    if not isinstance(object_types, dict) or not object_types:
        fail("objectTypes must be a non-empty object")

    for api_name, obj in object_types.items():
        pk = obj.get("primaryKey")
        props = obj.get("properties", {})
        if not pk:
            fail(f"{api_name}: primaryKey is required")
        if pk not in props:
            fail(f"{api_name}: primaryKey {pk!r} is not declared in properties")

    for link_name, link in schema["linkTypes"].items():
        if link.get("from") not in object_types:
            fail(f"{link_name}: unknown from object type {link.get('from')!r}")
        if link.get("to") not in object_types:
            fail(f"{link_name}: unknown to object type {link.get('to')!r}")
        if link.get("cardinality") not in {"one-to-one", "one-to-many", "many-to-one", "many-to-many"}:
            fail(f"{link_name}: invalid cardinality")

    valid_targets = set(object_types) | set(schema["linkTypes"])
    for action_name, action in schema["actionTypes"].items():
        if action.get("target") not in valid_targets:
            fail(f"{action_name}: unknown target {action.get('target')!r}")
        if action.get("operation") not in {"create", "modify", "delete", "link", "unlink"}:
            fail(f"{action_name}: invalid operation")


def validate_data(schema: dict, data: dict) -> None:
    objects = data.get("objects", {})
    for object_name, rows in objects.items():
        if object_name not in schema["objectTypes"]:
            fail(f"data contains undeclared object type: {object_name}")
        pk = schema["objectTypes"][object_name]["primaryKey"]
        seen = set()
        for row in rows:
            value = row.get(pk)
            if not value:
                fail(f"{object_name}: missing primary key {pk}")
            if value in seen:
                fail(f"{object_name}: duplicate primary key {value!r}")
            seen.add(value)

    categories = {row["categoryId"] for row in objects.get("Category", [])}
    tools = {row["toolId"] for row in objects.get("Tool", [])}
    for edge in data.get("links", {}).get("contains", []):
        if edge.get("categoryId") not in categories:
            fail(f"contains: unknown categoryId {edge.get('categoryId')!r}")
        if edge.get("toolId") not in tools:
            fail(f"contains: unknown toolId {edge.get('toolId')!r}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--schema", default="ontology/schema.json")
    parser.add_argument("--data")
    args = parser.parse_args()

    try:
        schema = load(args.schema)
        validate_schema(schema)
        if args.data:
            validate_data(schema, load(args.data))
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"ONTOLOGY INVALID: {exc}", file=sys.stderr)
        return 1

    print("ONTOLOGY VALID")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
