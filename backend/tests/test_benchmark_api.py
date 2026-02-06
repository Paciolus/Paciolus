"""
Tests for Benchmark API Endpoints.

Sprint 45: Benchmark Comparison Engine

Tests cover:
- GET /benchmarks/industries - List available industries
- GET /benchmarks/sources - Get source attribution
- GET /benchmarks/{industry} - Get industry benchmarks
- POST /benchmarks/compare - Compare ratios to benchmarks
"""

import pytest
import httpx
from unittest.mock import MagicMock

# Import from parent directory
import sys
sys.path.insert(0, '..')

from main import app, require_verified_user
from models import Industry


# =============================================================================
# TEST CLIENT SETUP
# =============================================================================

@pytest.fixture
def mock_user():
    """Create a mock user for authenticated endpoints."""
    user = MagicMock()
    user.id = 1
    user.email = "test@example.com"
    return user


@pytest.fixture
def override_auth(mock_user):
    """Override authentication for protected endpoints."""
    app.dependency_overrides[require_verified_user] = lambda: mock_user
    yield
    app.dependency_overrides.clear()


# =============================================================================
# TEST: GET /benchmarks/industries
# =============================================================================

class TestGetBenchmarkIndustries:
    """Tests for GET /benchmarks/industries endpoint."""

    @pytest.mark.asyncio
    async def test_returns_list(self):
        """Test that endpoint returns a list of industries."""
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.get("/benchmarks/industries")
            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_includes_priority_industries(self):
        """Test that all 6 priority industries are included."""
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.get("/benchmarks/industries")
            data = response.json()

            priority_industries = [
                "retail",
                "manufacturing",
                "professional_services",
                "technology",
                "healthcare",
                "financial_services"
            ]

            for industry in priority_industries:
                assert industry in data, f"Missing priority industry: {industry}"

    @pytest.mark.asyncio
    async def test_no_auth_required(self):
        """Test that endpoint doesn't require authentication."""
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            # No auth headers provided
            response = await client.get("/benchmarks/industries")
            assert response.status_code == 200


# =============================================================================
# TEST: GET /benchmarks/sources
# =============================================================================

class TestGetBenchmarkSources:
    """Tests for GET /benchmarks/sources endpoint."""

    @pytest.mark.asyncio
    async def test_returns_sources(self):
        """Test that endpoint returns source information."""
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.get("/benchmarks/sources")
            assert response.status_code == 200
            data = response.json()
            assert "primary_sources" in data
            assert "disclaimer" in data

    @pytest.mark.asyncio
    async def test_has_primary_sources(self):
        """Test that primary sources are listed."""
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.get("/benchmarks/sources")
            data = response.json()
            assert len(data["primary_sources"]) > 0

    @pytest.mark.asyncio
    async def test_has_coverage_info(self):
        """Test that coverage information is included."""
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.get("/benchmarks/sources")
            data = response.json()
            assert "coverage" in data
            assert "industries" in data["coverage"]

    @pytest.mark.asyncio
    async def test_has_disclaimer(self):
        """Test that disclaimer is included."""
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.get("/benchmarks/sources")
            data = response.json()
            assert len(data["disclaimer"]) > 50  # Meaningful disclaimer

    @pytest.mark.asyncio
    async def test_lists_available_industries(self):
        """Test that available industries are listed."""
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.get("/benchmarks/sources")
            data = response.json()
            assert "available_industries" in data
            assert len(data["available_industries"]) >= 6


# =============================================================================
# TEST: GET /benchmarks/{industry}
# =============================================================================

class TestGetIndustryBenchmarks:
    """Tests for GET /benchmarks/{industry} endpoint."""

    @pytest.mark.asyncio
    async def test_get_retail_benchmarks(self):
        """Test getting retail industry benchmarks."""
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.get("/benchmarks/retail")
            assert response.status_code == 200
            data = response.json()
            assert data["industry"] == "retail"

    @pytest.mark.asyncio
    async def test_get_manufacturing_benchmarks(self):
        """Test getting manufacturing industry benchmarks."""
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.get("/benchmarks/manufacturing")
            assert response.status_code == 200
            data = response.json()
            assert data["industry"] == "manufacturing"

    @pytest.mark.asyncio
    async def test_benchmark_structure(self):
        """Test that benchmark response has correct structure."""
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.get("/benchmarks/retail")
            data = response.json()

            assert "industry" in data
            assert "fiscal_year" in data
            assert "benchmarks" in data
            assert "source_attribution" in data
            assert "data_quality_score" in data
            assert "available_ratios" in data

    @pytest.mark.asyncio
    async def test_benchmark_has_percentiles(self):
        """Test that benchmarks include percentile data."""
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.get("/benchmarks/retail")
            data = response.json()

            # Check current_ratio benchmark
            assert "current_ratio" in data["benchmarks"]
            cr = data["benchmarks"]["current_ratio"]

            assert "p10" in cr
            assert "p25" in cr
            assert "p50" in cr
            assert "p75" in cr
            assert "p90" in cr
            assert "mean" in cr
            assert "std_dev" in cr
            assert "sample_size" in cr

    @pytest.mark.asyncio
    async def test_percentiles_ordered(self):
        """Test that percentiles are in ascending order."""
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.get("/benchmarks/retail")
            data = response.json()

            for ratio_name, benchmark in data["benchmarks"].items():
                assert benchmark["p10"] <= benchmark["p25"], f"{ratio_name}: p10 > p25"
                assert benchmark["p25"] <= benchmark["p50"], f"{ratio_name}: p25 > p50"
                assert benchmark["p50"] <= benchmark["p75"], f"{ratio_name}: p50 > p75"
                assert benchmark["p75"] <= benchmark["p90"], f"{ratio_name}: p75 > p90"

    @pytest.mark.asyncio
    async def test_invalid_industry_404(self):
        """Test that invalid industry returns 404."""
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.get("/benchmarks/invalid_industry")
            assert response.status_code == 404
            assert "not found" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_unavailable_industry_404(self):
        """Test that unsupported industry returns 404."""
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.get("/benchmarks/education")
            assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_fiscal_year_parameter(self):
        """Test that fiscal_year query parameter works."""
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.get("/benchmarks/retail?fiscal_year=2025")
            assert response.status_code == 200
            data = response.json()
            assert data["fiscal_year"] == 2025

    @pytest.mark.asyncio
    async def test_available_ratios_listed(self):
        """Test that available ratios are listed."""
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.get("/benchmarks/retail")
            data = response.json()

            assert len(data["available_ratios"]) >= 8
            assert "current_ratio" in data["available_ratios"]
            assert "gross_margin" in data["available_ratios"]


# =============================================================================
# TEST: POST /benchmarks/compare
# =============================================================================

class TestCompareToBenchmarks:
    """Tests for POST /benchmarks/compare endpoint."""

    @pytest.mark.asyncio
    async def test_requires_authentication(self):
        """Test that endpoint requires authentication."""
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            payload = {
                "ratios": {"current_ratio": 1.5},
                "industry": "retail"
            }
            response = await client.post("/benchmarks/compare", json=payload)
            assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_compare_single_ratio(self, mock_user):
        """Test comparing a single ratio."""
        app.dependency_overrides[require_verified_user] = lambda: mock_user

        try:
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app),
                base_url="http://test"
            ) as client:
                payload = {
                    "ratios": {"current_ratio": 1.65},
                    "industry": "retail"
                }
                response = await client.post("/benchmarks/compare", json=payload)
                assert response.status_code == 200
                data = response.json()

                assert "comparisons" in data
                assert len(data["comparisons"]) == 1
                assert data["comparisons"][0]["ratio_name"] == "current_ratio"
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_compare_multiple_ratios(self, mock_user):
        """Test comparing multiple ratios."""
        app.dependency_overrides[require_verified_user] = lambda: mock_user

        try:
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app),
                base_url="http://test"
            ) as client:
                payload = {
                    "ratios": {
                        "current_ratio": 1.80,
                        "gross_margin": 0.35,
                        "debt_to_equity": 1.20
                    },
                    "industry": "retail"
                }
                response = await client.post("/benchmarks/compare", json=payload)
                assert response.status_code == 200
                data = response.json()

                assert len(data["comparisons"]) == 3
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_comparison_structure(self, mock_user):
        """Test that comparison response has correct structure."""
        app.dependency_overrides[require_verified_user] = lambda: mock_user

        try:
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app),
                base_url="http://test"
            ) as client:
                payload = {
                    "ratios": {"current_ratio": 1.80},
                    "industry": "retail"
                }
                response = await client.post("/benchmarks/compare", json=payload)
                data = response.json()

                # Check top-level structure
                assert "industry" in data
                assert "fiscal_year" in data
                assert "comparisons" in data
                assert "overall_score" in data
                assert "overall_health" in data
                assert "source_attribution" in data
                assert "generated_at" in data
                assert "disclaimer" in data

                # Check comparison structure
                comp = data["comparisons"][0]
                assert "ratio_name" in comp
                assert "client_value" in comp
                assert "percentile" in comp
                assert "percentile_label" in comp
                assert "position" in comp
                assert "interpretation" in comp
                assert "health_indicator" in comp
                assert "benchmark_median" in comp
                assert "benchmark_mean" in comp
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_percentile_at_median(self, mock_user):
        """Test that value at median returns ~50th percentile."""
        app.dependency_overrides[require_verified_user] = lambda: mock_user

        try:
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app),
                base_url="http://test"
            ) as client:
                # Retail current_ratio median (p50) is 1.65
                payload = {
                    "ratios": {"current_ratio": 1.65},
                    "industry": "retail"
                }
                response = await client.post("/benchmarks/compare", json=payload)
                data = response.json()

                comp = data["comparisons"][0]
                assert comp["percentile"] == 50
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_overall_score_calculated(self, mock_user):
        """Test that overall score is calculated."""
        app.dependency_overrides[require_verified_user] = lambda: mock_user

        try:
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app),
                base_url="http://test"
            ) as client:
                payload = {
                    "ratios": {
                        "current_ratio": 2.50,  # Above median
                        "gross_margin": 0.45,   # Above median
                    },
                    "industry": "retail"
                }
                response = await client.post("/benchmarks/compare", json=payload)
                data = response.json()

                assert data["overall_score"] > 50  # Above average
                assert data["overall_health"] in ["strong", "moderate", "concerning"]
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_invalid_industry_400(self, mock_user):
        """Test that invalid industry returns 400."""
        app.dependency_overrides[require_verified_user] = lambda: mock_user

        try:
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app),
                base_url="http://test"
            ) as client:
                payload = {
                    "ratios": {"current_ratio": 1.5},
                    "industry": "invalid_industry"
                }
                response = await client.post("/benchmarks/compare", json=payload)
                assert response.status_code == 400
                assert "not found" in response.json()["detail"].lower()
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_no_matching_ratios_400(self, mock_user):
        """Test that no matching ratios returns 400."""
        app.dependency_overrides[require_verified_user] = lambda: mock_user

        try:
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app),
                base_url="http://test"
            ) as client:
                payload = {
                    "ratios": {"nonexistent_ratio": 1.5},
                    "industry": "retail"
                }
                response = await client.post("/benchmarks/compare", json=payload)
                assert response.status_code == 400
                assert "none of the provided ratios" in response.json()["detail"].lower()
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_disclaimer_included(self, mock_user):
        """Test that disclaimer is included in response."""
        app.dependency_overrides[require_verified_user] = lambda: mock_user

        try:
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app),
                base_url="http://test"
            ) as client:
                payload = {
                    "ratios": {"current_ratio": 1.5},
                    "industry": "retail"
                }
                response = await client.post("/benchmarks/compare", json=payload)
                data = response.json()

                assert "disclaimer" in data
                assert len(data["disclaimer"]) > 50
                assert "professional judgment" in data["disclaimer"].lower()
        finally:
            app.dependency_overrides.clear()


# =============================================================================
# TEST: ZERO-STORAGE COMPLIANCE
# =============================================================================

class TestZeroStorageCompliance:
    """Tests verifying Zero-Storage compliance for benchmark API."""

    @pytest.mark.asyncio
    async def test_benchmarks_public_no_client_data(self):
        """Test that GET /benchmarks/{industry} returns only public data."""
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.get("/benchmarks/retail")
            data = response.json()

            # Should only contain aggregate industry data, no client identifiers
            assert "user_id" not in str(data)
            assert "client_id" not in str(data)
            assert "email" not in str(data)

    @pytest.mark.asyncio
    async def test_comparison_ephemeral(self, mock_user):
        """Test that comparison results are computed in real-time."""
        app.dependency_overrides[require_verified_user] = lambda: mock_user

        try:
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app),
                base_url="http://test"
            ) as client:
                payload = {
                    "ratios": {"current_ratio": 1.80},
                    "industry": "retail"
                }

                # Make two identical requests
                response1 = await client.post("/benchmarks/compare", json=payload)
                response2 = await client.post("/benchmarks/compare", json=payload)

                data1 = response1.json()
                data2 = response2.json()

                # Results should be identical (same input = same output)
                assert data1["comparisons"][0]["percentile"] == data2["comparisons"][0]["percentile"]

                # generated_at is present
                assert "generated_at" in data1
                assert "generated_at" in data2
        finally:
            app.dependency_overrides.clear()


# =============================================================================
# TEST: INDUSTRY-SPECIFIC BENCHMARKS
# =============================================================================

class TestIndustrySpecificBenchmarks:
    """Tests for industry-specific benchmark characteristics."""

    @pytest.mark.asyncio
    async def test_financial_services_high_leverage(self):
        """Test that financial services has higher D/E benchmarks."""
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            retail = (await client.get("/benchmarks/retail")).json()
            finserv = (await client.get("/benchmarks/financial_services")).json()

            retail_de = retail["benchmarks"]["debt_to_equity"]["p50"]
            finserv_de = finserv["benchmarks"]["debt_to_equity"]["p50"]

            assert finserv_de > retail_de, "Financial services should have higher leverage"

    @pytest.mark.asyncio
    async def test_technology_high_liquidity(self):
        """Test that technology has higher current ratio benchmarks."""
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            retail = (await client.get("/benchmarks/retail")).json()
            tech = (await client.get("/benchmarks/technology")).json()

            retail_cr = retail["benchmarks"]["current_ratio"]["p50"]
            tech_cr = tech["benchmarks"]["current_ratio"]["p50"]

            assert tech_cr > retail_cr, "Technology should have higher liquidity"

    @pytest.mark.asyncio
    async def test_professional_services_higher_margins(self):
        """Test that professional services has higher gross margins."""
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            retail = (await client.get("/benchmarks/retail")).json()
            ps = (await client.get("/benchmarks/professional_services")).json()

            retail_gm = retail["benchmarks"]["gross_margin"]["p50"]
            ps_gm = ps["benchmarks"]["gross_margin"]["p50"]

            assert ps_gm > retail_gm, "Professional services should have higher margins"

    @pytest.mark.asyncio
    async def test_manufacturing_has_asset_turnover(self):
        """Test that manufacturing includes asset turnover."""
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.get("/benchmarks/manufacturing")
            data = response.json()

            assert "asset_turnover" in data["benchmarks"]
