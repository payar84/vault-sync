"""Schema validation for secret values against expected types and patterns."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional


class FieldType(str, Enum):
    STRING = "string"
    INTEGER = "integer"
    BOOLEAN = "boolean"
    URL = "url"
    EMAIL = "email"


@dataclass
class FieldSchema:
    name: str
    type: FieldType = FieldType.STRING
    required: bool = True
    pattern: Optional[str] = None

    def validate_value(self, value: str) -> Optional[str]:
        """Return an error message or None if valid."""
        if self.type == FieldType.INTEGER:
            if not value.lstrip("-").isdigit():
                return f"{self.name}: expected integer, got {value!r}"
        elif self.type == FieldType.BOOLEAN:
            if value.lower() not in ("true", "false", "1", "0"):
                return f"{self.name}: expected boolean, got {value!r}"
        elif self.type == FieldType.URL:
            if not re.match(r"^https?://", value):
                return f"{self.name}: expected URL starting with http(s)://, got {value!r}"
        elif self.type == FieldType.EMAIL:
            if not re.match(r"^[^@]+@[^@]+\.[^@]+$", value):
                return f"{self.name}: expected email address, got {value!r}"
        if self.pattern and not re.fullmatch(self.pattern, value):
            return f"{self.name}: value {value!r} does not match pattern {self.pattern!r}"
        return None


@dataclass
class SecretSchema:
    fields: List[FieldSchema] = field(default_factory=list)

    def validate(self, secrets: Dict[str, str]) -> List[str]:
        """Validate a dict of secrets and return a list of error messages."""
        errors: List[str] = []
        for f in self.fields:
            if f.name not in secrets:
                if f.required:
                    errors.append(f"{f.name}: required key is missing")
                continue
            err = f.validate_value(secrets[f.name])
            if err:
                errors.append(err)
        return errors
