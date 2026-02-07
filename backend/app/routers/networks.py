"""
Network & Clearing Core API: CRUD, metrics, exposure matrix.
"""
from fastapi import APIRouter, HTTPException

from ..schemas.network import (
    NetworkCreate,
    NetworkResponse,
    NetworkMetricsResponse,
    InstitutionResponse,
    ExposureResponse,
)
from ..services.network_service import NetworkService, network_store

router = APIRouter()


@router.post("/", response_model=NetworkResponse)
async def create_network(payload: NetworkCreate):
    """Create a new financial network with institutions and exposures."""
    institutions_data = [i.model_dump() for i in payload.institutions]
    exposures_data = [e.model_dump() for e in payload.exposures]
    net = NetworkService.create_network(
        payload.id,
        payload.name,
        institutions_data,
        exposures_data,
    )
    node_ids = list(net.graph.nodes())
    return NetworkResponse(
        id=payload.id,
        name=payload.name or payload.id,
        institutions=[
            InstitutionResponse(
                id=inst.id,
                type=inst.type.value,
                capital=inst.capital,
                assets=inst.assets,
                liabilities=inst.liabilities,
                risk_aversion=inst.risk_aversion,
                systemic_awareness=inst.systemic_awareness,
            )
            for inst in net.institutions.values()
        ],
        exposures=[
            ExposureResponse(
                creditor_id=e.creditor_id,
                debtor_id=e.debtor_id,
                amount=e.amount,
                maturity_days=e.maturity_days,
                interest_rate=e.interest_rate,
                collateral=e.collateral,
            )
            for e in net.exposures
        ],
        node_ids=node_ids,
    )


@router.get("/")
async def list_networks():
    """List all stored networks."""
    return {"networks": NetworkService.list_networks()}


@router.get("/{network_id}", response_model=NetworkResponse)
async def get_network(network_id: str):
    """Get a network by id."""
    net = NetworkService.get_network(network_id)
    if net is None:
        raise HTTPException(status_code=404, detail="Network not found")
    name = NetworkService.get_name(network_id) or network_id
    return NetworkResponse(
        id=network_id,
        name=name,
        institutions=[
            InstitutionResponse(
                id=inst.id,
                type=inst.type.value,
                capital=inst.capital,
                assets=inst.assets,
                liabilities=inst.liabilities,
                risk_aversion=inst.risk_aversion,
                systemic_awareness=inst.systemic_awareness,
            )
            for inst in net.institutions.values()
        ],
        exposures=[
            ExposureResponse(
                creditor_id=e.creditor_id,
                debtor_id=e.debtor_id,
                amount=e.amount,
                maturity_days=e.maturity_days,
                interest_rate=e.interest_rate,
                collateral=e.collateral,
            )
            for e in net.exposures
        ],
        node_ids=list(net.graph.nodes()),
    )


@router.get("/{network_id}/metrics", response_model=NetworkMetricsResponse)
async def get_network_metrics(network_id: str):
    """Get network metrics: centrality, stability, exposure matrix, capital vector."""
    net = NetworkService.get_network(network_id)
    if net is None:
        raise HTTPException(status_code=404, detail="Network not found")

    metrics = net.compute_network_metrics()
    stability = net.check_stability()
    core_periphery = net.identify_core_periphery()

    W = net.get_exposure_matrix()
    C = net.get_capital_vector()
    node_ids = list(net.graph.nodes())

    return NetworkMetricsResponse(
        network_id=network_id,
        node_ids=node_ids,
        degree_centrality=metrics["degree_centrality"],
        betweenness_centrality=metrics["betweenness_centrality"],
        density=metrics["density"],
        avg_clustering=metrics["avg_clustering"],
        spectral_radius=stability["spectral_radius"],
        is_stable=stability["is_stable"],
        core_periphery=core_periphery,
        exposure_matrix=W.tolist(),
        capital_vector=C.tolist(),
    )


@router.delete("/{network_id}")
async def delete_network(network_id: str):
    """Delete a network."""
    if not NetworkService.delete_network(network_id):
        raise HTTPException(status_code=404, detail="Network not found")
    return {"status": "deleted", "network_id": network_id}
