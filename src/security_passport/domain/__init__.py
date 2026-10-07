"""Domain model — FACT / EVIDENCE / INFERENCE separation.

The three layers are never mixed: an ``Assertion`` is verbatim
provider output, a ``PassportField`` is the adjudicated projection,
and a ``RuleRef`` is a versioned derivation. See ADR-004.
"""
