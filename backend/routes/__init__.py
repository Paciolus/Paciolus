"""
Paciolus API — Route Registration
"""
from routes.health import router as health_router
from routes.auth_routes import router as auth_router
from routes.users import router as users_router
from routes.activity import router as activity_router
from routes.clients import router as clients_router
from routes.settings import router as settings_router
from routes.diagnostics import router as diagnostics_router
from routes.audit import router as audit_router
from routes.export import router as export_router
from routes.benchmarks import router as benchmarks_router
from routes.trends import router as trends_router
from routes.prior_period import router as prior_period_router
from routes.multi_period import router as multi_period_router
from routes.adjustments import router as adjustments_router
from routes.je_testing import router as je_testing_router
from routes.ap_testing import router as ap_testing_router
from routes.bank_reconciliation import router as bank_reconciliation_router
from routes.payroll_testing import router as payroll_testing_router
from routes.three_way_match import router as three_way_match_router
from routes.revenue_testing import router as revenue_testing_router
from routes.ar_aging import router as ar_aging_router
from routes.fixed_asset_testing import router as fixed_asset_testing_router
from routes.inventory_testing import router as inventory_testing_router
from routes.engagements import router as engagements_router
from routes.follow_up_items import router as follow_up_items_router
from routes.contact import router as contact_router
from routes.currency import router as currency_router

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
    ap_testing_router,
    bank_reconciliation_router,
    payroll_testing_router,
    three_way_match_router,
    revenue_testing_router,
    ar_aging_router,
    fixed_asset_testing_router,
    inventory_testing_router,
    engagements_router,
    follow_up_items_router,
    contact_router,
    currency_router,
]
