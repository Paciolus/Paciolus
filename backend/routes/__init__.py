"""
Paciolus API — Route Registration
"""

from routes.account_risk_heatmap import router as account_risk_heatmap_router
from routes.activity import router as activity_router
from routes.adjustments import router as adjustments_router
from routes.admin_dashboard import router as admin_dashboard_router
from routes.analytical_expectations import router as analytical_expectations_router
from routes.ap_testing import router as ap_testing_router
from routes.ar_aging import router as ar_aging_router
from routes.audit import router as audit_router
from routes.auth_routes import router as auth_router
from routes.bank_reconciliation import router as bank_reconciliation_router
from routes.benchmarks import router as benchmarks_router
from routes.billing import router as billing_router
from routes.book_to_tax import router as book_to_tax_router
from routes.branding import router as branding_router
from routes.bulk_upload import router as bulk_upload_router
from routes.cash_flow_projector import router as cash_flow_projector_router
from routes.clients import router as clients_router
from routes.composite_risk import router as composite_risk_router
from routes.contact import router as contact_router
from routes.currency import router as currency_router
from routes.depreciation import router as depreciation_router
from routes.diagnostics import router as diagnostics_router
from routes.engagements import router as engagements_router
from routes.export import router as export_router
from routes.export_sharing import router as export_sharing_router
from routes.fixed_asset_testing import router as fixed_asset_testing_router
from routes.follow_up_items import router as follow_up_items_router
from routes.form_1099 import router as form_1099_router
from routes.health import router as health_router
from routes.intercompany_elimination import router as intercompany_elimination_router
from routes.internal_admin import router as internal_admin_router
from routes.internal_metrics import router as internal_metrics_router
from routes.inventory_testing import router as inventory_testing_router
from routes.je_testing import router as je_testing_router
from routes.lease_accounting import router as lease_accounting_router
from routes.loan_amortization import router as loan_amortization_router
from routes.metrics import router as metrics_router
from routes.multi_period import router as multi_period_router
from routes.organization import router as organization_router
from routes.payroll_testing import router as payroll_testing_router
from routes.prior_period import router as prior_period_router
from routes.revenue_testing import router as revenue_testing_router
from routes.sampling import router as sampling_router
from routes.settings import router as settings_router
from routes.sod import router as sod_router
from routes.three_way_match import router as three_way_match_router
from routes.trends import router as trends_router
from routes.uncorrected_misstatements import router as uncorrected_misstatements_router
from routes.users import router as users_router
from routes.w2_reconciliation import router as w2_reconciliation_router

all_routers = [
    health_router,
    auth_router,
    users_router,
    activity_router,
    clients_router,
    settings_router,
    diagnostics_router,
    audit_router,
    export_router,
    benchmarks_router,
    trends_router,
    prior_period_router,
    multi_period_router,
    adjustments_router,
    je_testing_router,
    loan_amortization_router,
    cash_flow_projector_router,
    book_to_tax_router,
    depreciation_router,
    lease_accounting_router,
    ap_testing_router,
    bank_reconciliation_router,
    payroll_testing_router,
    three_way_match_router,
    revenue_testing_router,
    ar_aging_router,
    fixed_asset_testing_router,
    form_1099_router,
    inventory_testing_router,
    engagements_router,
    follow_up_items_router,
    analytical_expectations_router,
    uncorrected_misstatements_router,
    contact_router,
    currency_router,
    sampling_router,
    billing_router,
    metrics_router,
    organization_router,
    export_sharing_router,
    admin_dashboard_router,
    branding_router,
    bulk_upload_router,
    composite_risk_router,
    account_risk_heatmap_router,
    sod_router,
    internal_metrics_router,
    internal_admin_router,
    w2_reconciliation_router,
    intercompany_elimination_router,
]
