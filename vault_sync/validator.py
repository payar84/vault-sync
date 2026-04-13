"""Validates secret values against expected constraints before writing."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional
import re


@dataclass
class ValidationRule:
    key: str
    required: bool = True
    min_length: Optional[int] = None
    max_length: Optional[int] = None
    pattern: Optional[str] = None

    def validate(self, value: Optional[str]) -> List[str]:
        errors: List[str] = []
        if value is None or value == "":
            if self.required:
                errors.append(f"{self.key}: value is required but missing")
            return errors
        if self.min_length is not None and len(value) < self.min_length:
            errors.append(
                f"{self.key}: length {len(value)} is below minimum {self.min_length}"
            )
        if self.max_length is not None and len(value) > self.max_length:
            errors.append(
                f"{self.key}: length {len(value)} exceeds maximum {self.max_length}"
            )
        if self.pattern is not None and not re.fullmatch(self.pattern, value):
            errors.append(
                f"{self.key}: value does not match pattern '{self.pattern}'"
            )
        return errors


@dataclass
class ValidationResult:
    errors: List[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return len(self.errors) == 0

    def __repr__(self) -> str:  # pragma: no cover
        status = "ok" if self.ok else f"{len(self.errors)} error(s)"
        return f"ValidationResult({status})"


def validate_secrets(
    secrets: Dict[str, str],
    rules: List[ValidationRule],
) -> ValidationResult:
    """Run all rules against the provided secrets dict."""
    all_errors: List[str] = []
    for rule in rules:
        value = secrets.get(rule.key)
        all_errors.extend(rule.validate(value))
    return ValidationResult(errors=all_errors)


def parse_rules(raw: List[Dict]) -> List[ValidationRule]:
    """Build ValidationRule objects from plain dicts (e.g. loaded from JSON)."""
    rules = []
    for item in raw:
        rules.append(
            ValidationRule(
                key=item["key"],
                required=item.get("required", True),
                min_length=item.get("min_length"),
                max_length=item.get("max_length"),
                pattern=item.get("pattern"),
            )
        )
    return rules
