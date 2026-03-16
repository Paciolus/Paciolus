"""
Flux analysis service — extracted from audit.py.

Encapsulates the trial-balance-pair processing logic that was previously
inlined in the /audit/flux endpoint handler.
"""

from audit_engine import DEFAULT_CHUNK_SIZE, StreamingAuditor, process_tb_chunked
from flux_engine import FluxEngine
from recon_engine import ReconEngine


def _process_period(file_bytes: bytes, filename: str, materiality: float) -> dict:
    """Process a single period's TB file into a balance dict."""
    auditor = StreamingAuditor(materiality_threshold=materiality)
    for chunk, rows in process_tb_chunked(file_bytes, filename, DEFAULT_CHUNK_SIZE):
        auditor.process_chunk(chunk, rows)
        del chunk

    classified = auditor.get_classified_accounts()
    balances = {}
    for acct, bals in auditor.account_balances.items():
        net = bals["debit"] - bals["credit"]
        acct_type = classified.get(acct, "Unknown")
        balances[acct] = {
            "net": net,
            "type": acct_type,
            "debit": bals["debit"],
            "credit": bals["credit"],
        }

    auditor.clear()
    del auditor
    return balances


def run_flux_analysis(
    content_curr: bytes,
    curr_filename: str,
    content_prior: bytes,
    prior_filename: str,
    materiality: float,
) -> tuple:
    """Run the full flux analysis pipeline on two TB files.

    Returns (flux_result, recon_result) — both are domain objects with
    .to_dict() methods.
    """
    current_balances = _process_period(content_curr, curr_filename, materiality)
    prior_balances = _process_period(content_prior, prior_filename, materiality)

    flux_engine = FluxEngine(materiality_threshold=materiality)
    flux_result = flux_engine.compare(current_balances, prior_balances)

    recon_engine = ReconEngine(materiality_threshold=materiality)
    recon_result = recon_engine.calculate_scores(flux_result)

    return flux_result, recon_result
