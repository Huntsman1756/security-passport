"""cnmv_iic (OpenFunds) registry adapter — ES IIC share-class
roles. Read surface over the upstream monthly registry dataset
(share_classes + funds parquets).

Upstream semantics preserved verbatim: fund_key /
compartment_key / share_class_key grain, entity_type,
gestora/depositario *names* as the registry reports them.
A gestora's identity is NEVER promoted to issuer LEI — roles are
roles.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

PARSER = "security_passport.providers.openfunds"
PARSER_VERSION = "1"
PROVIDER = "openfunds_cnmv_iic"


@dataclass(frozen=True)
class FundRoleRecord:
    isin: str
    share_class_key: str
    fund_key: str
    compartment_key: str
    entity_type: str
    fund_name: str
    share_class_name: str
    compartment_name: str
    manager_name: str           # gestora_denominacion — a role
    depositary_name: str        # depositario_denominacion — a role
    manager_reg_number: str
    depositary_reg_number: str
    period: str
    source_artifact_id: str


def normalize_row(sc: dict[str, Any],
                    fu: dict[str, Any]) -> FundRoleRecord:
    return FundRoleRecord(
        isin=sc["isin_raw"],
        share_class_key=sc["share_class_key"],
        fund_key=sc["fund_key"],
        compartment_key=sc["compartment_key"],
        entity_type=sc.get("entity_type") or "",
        fund_name=fu.get("denominacion") or "",
        share_class_name=sc.get("denominacion_clase") or "",
        compartment_name=sc.get("denominacion_compartimento") or "",
        manager_name=fu.get("gestora_denominacion") or "",
        depositary_name=fu.get("depositario_denominacion") or "",
        manager_reg_number=str(
            fu.get("gestora_numero_registro") or ""),
        depositary_reg_number=str(
            fu.get("depositario_numero_registro") or ""),
        period=sc.get("period") or "",
        source_artifact_id=sc.get("source_artifact_id") or "")
