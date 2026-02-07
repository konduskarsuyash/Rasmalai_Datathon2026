"""
Network & Clearing Core: build and store FinancialNetwork from API payloads.
Uses core_implementation.FinancialNetwork, Institution, Exposure, InstitutionType.
"""
from typing import Dict, List

from core_implementation import (
    FinancialNetwork,
    Institution,
    Exposure,
    InstitutionType,
)

# In-memory store: network_id -> (FinancialNetwork, optional name)
network_store: Dict[str, tuple] = {}


def _institution_type(s: str) -> InstitutionType:
    v = s.lower().strip()
    if v == "bank":
        return InstitutionType.BANK
    if v in ("hedge_fund", "hedge fund"):
        return InstitutionType.HEDGE_FUND
    if v in ("clearing_house", "clearing house"):
        return InstitutionType.CLEARING_HOUSE
    if v == "insurance":
        return InstitutionType.INSURANCE
    return InstitutionType.BANK


class NetworkService:
    @staticmethod
    def create_network(network_id: str, name: str | None, institutions: list, exposures: list) -> FinancialNetwork:
        net = FinancialNetwork()
        for i in institutions:
            inst = Institution(
                id=i["id"],
                type=_institution_type(i["type"]),
                capital=float(i["capital"]),
                assets=float(i["assets"]),
                liabilities=float(i["liabilities"]),
                risk_aversion=float(i.get("risk_aversion", 1.0)),
                systemic_awareness=float(i.get("systemic_awareness", 0.1)),
            )
            net.add_institution(inst)
        for e in exposures:
            exp = Exposure(
                creditor_id=e["creditor_id"],
                debtor_id=e["debtor_id"],
                amount=float(e["amount"]),
                maturity_days=int(e["maturity_days"]),
                interest_rate=float(e.get("interest_rate", 0.02)),
                collateral=float(e.get("collateral", 0.0)),
            )
            net.add_exposure(exp)
        network_store[network_id] = (net, name or network_id)
        return net

    @staticmethod
    def get_network(network_id: str) -> FinancialNetwork | None:
        if network_id not in network_store:
            return None
        return network_store[network_id][0]

    @staticmethod
    def get_name(network_id: str) -> str | None:
        if network_id not in network_store:
            return None
        return network_store[network_id][1]

    @staticmethod
    def list_networks() -> List[dict]:
        return [
            {"id": nid, "name": name or nid}
            for nid, (_, name) in network_store.items()
        ]

    @staticmethod
    def delete_network(network_id: str) -> bool:
        if network_id in network_store:
            del network_store[network_id]
            return True
        return False
