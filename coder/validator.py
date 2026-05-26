"""
coder/validator.py — lightweight post-generation checks for ServUO C# output.

Does not compile the code. Runs fast regex/string heuristics to catch
common LLM mistakes before the code is written to disk or sent to the client.
"""

import re
from dataclasses import dataclass, field


@dataclass
class ValidationResult:
    ok: bool
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {"ok": self.ok, "warnings": self.warnings}


REQUIRED_PATTERNS: list[tuple[str, str]] = [
    (r"using Server",                         "Missing 'using Server;'"),
    (r"namespace\s+\w",                       "Missing namespace declaration"),
    (r"public\s+(class|static\s+class)\s+\w", "Missing public class declaration"),
    (r"Serialize\s*\(",                       "Missing Serialize() override — required for persistence"),
    (r"Deserialize\s*\(",                     "Missing Deserialize() override — required for persistence"),
]

FORBIDDEN_PATTERNS: list[tuple[str, str]] = [
    (r"TODO",                                  "Contains TODO placeholder"),
    (r"throw new NotImplementedException",     "Contains NotImplementedException — implement all methods"),
    (r"Console\.Write",                        "Use shard logging or SendMessage instead of Console.Write"),
    (r"\.Result\b",                            "Blocking .Result on async Task — use Timer.DelayCall pattern instead"),
]


def validate(code: str) -> ValidationResult:
    warnings: list[str] = []
    for pattern, message in REQUIRED_PATTERNS:
        if not re.search(pattern, code):
            warnings.append(f"[MISSING] {message}")
    for pattern, message in FORBIDDEN_PATTERNS:
        if re.search(pattern, code):
            warnings.append(f"[FORBIDDEN] {message}")
    if code.count("{") != code.count("}"):
        warnings.append(
            f"[SYNTAX] Unbalanced braces: {code.count('{')} open vs {code.count('}')} close"
        )
    return ValidationResult(ok=not warnings, warnings=warnings)
