"""
Tests for summary and analytics endpoints.
"""

from datetime import date, timedelta
from fastapi.testclient import TestClient


class TestFinancialSummary:
    """Tests for financial summary endpoint."""
    
    def test_empty_summary(self, client, auth_headers):
        """Test summary with no transactions."""
        response = client.get("/api/summaries/overview", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total_income"] == 0
        assert data["total_expenses"] == 0
        assert data["balance"] == 0
        assert data["transaction_count"] == 0
    
    def test_summary_with_transactions(self, client, analyst_auth_headers):
        """Test summary with transactions."""
        # Create income
        client.post(
            "/api/transactions",
            json={
                "amount": 1000,
                "type": "income",
                "category": "Salary",
                "date": str(date.today())
            },
            headers=analyst_auth_headers
        )
        
        # Create expenses
        client.post(
            "/api/transactions",
            json={
                "amount": 200,
                "type": "expense",
                "category": "Food",
                "date": str(date.today())
            },
            headers=analyst_auth_headers
        )
        client.post(
            "/api/transactions",
            json={
                "amount": 100,
                "type": "expense",
                "category": "Transport",
                "date": str(date.today())
            },
            headers=analyst_auth_headers
        )
        
        response = client.get("/api/summaries/overview", headers=analyst_auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total_income"] == 1000
        assert data["total_expenses"] == 300
        assert data["balance"] == 700
        assert data["transaction_count"] == 3
    
    def test_summary_with_date_filter(self, client, analyst_auth_headers):
        """Test summary with date filtering."""
        today = date.today()
        last_month = today - timedelta(days=30)
        
        # Create transaction for today
        client.post(
            "/api/transactions",
            json={
                "amount": 500,
                "type": "income",
                "category": "Bonus",
                "date": str(today)
            },
            headers=analyst_auth_headers
        )
        
        # Create transaction for last month
        client.post(
            "/api/transactions",
            json={
                "amount": 200,
                "type": "income",
                "category": "Old Bonus",
                "date": str(last_month)
            },
            headers=analyst_auth_headers
        )
        
        # Filter to only include this week
        week_ago = today - timedelta(days=7)
        response = client.get(
            f"/api/summaries/overview?date_from={week_ago}&date_to={today}",
            headers=analyst_auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total_income"] == 500
        assert data["transaction_count"] == 1


class TestCategoryBreakdown:
    """Tests for category breakdown endpoint."""
    
    def test_category_breakdown_empty(self, client, auth_headers):
        """Test breakdown with no transactions."""
        response = client.get("/api/summaries/by-category", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total_transactions"] == 0
        assert data["categories"] == []
    
    def test_category_breakdown_with_data(self, client, analyst_auth_headers):
        """Test category breakdown with transactions."""
        # Create transactions in different categories
        for i in range(5):
            client.post(
                "/api/transactions",
                json={
                    "amount": 100 * (i + 1),
                    "type": "expense",
                    "category": f"Category{i % 2}",
                    "date": str(date.today())
                },
                headers=analyst_auth_headers
            )
        
        response = client.get("/api/summaries/by-category", headers=analyst_auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total_transactions"] == 5
        assert len(data["categories"]) == 2
        
        # Check that categories are sorted by total
        if len(data["categories"]) > 1:
            assert data["categories"][0]["total"] >= data["categories"][1]["total"]
    
    def test_category_breakdown_filter_by_type(self, client, analyst_auth_headers):
        """Test category breakdown filtered by type."""
        # Create income
        client.post(
            "/api/transactions",
            json={
                "amount": 1000,
                "type": "income",
                "category": "Salary",
                "date": str(date.today())
            },
            headers=analyst_auth_headers
        )
        
        # Create expense
        client.post(
            "/api/transactions",
            json={
                "amount": 100,
                "type": "expense",
                "category": "Food",
                "date": str(date.today())
            },
            headers=analyst_auth_headers
        )
        
        # Filter by income only
        response = client.get(
            "/api/summaries/by-category?type=income",
            headers=analyst_auth_headers
        )
        data = response.json()
        assert data["total_transactions"] == 1
        assert data["categories"][0]["category"] == "Salary"


class TestMonthlySummary:
    """Tests for monthly summary endpoint."""
    
    def test_monthly_summary_empty(self, client, auth_headers):
        """Test monthly summary with no transactions."""
        response = client.get("/api/summaries/monthly", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["monthly_data"] == []
        assert data["total_income"] == 0
    
    def test_monthly_summary_with_data(self, client, analyst_auth_headers):
        """Test monthly summary with transactions."""
        # Create transactions
        client.post(
            "/api/transactions",
            json={
                "amount": 1000,
                "type": "income",
                "category": "Salary",
                "date": str(date.today())
            },
            headers=analyst_auth_headers
        )
        client.post(
            "/api/transactions",
            json={
                "amount": 200,
                "type": "expense",
                "category": "Food",
                "date": str(date.today())
            },
            headers=analyst_auth_headers
        )
        
        response = client.get("/api/summaries/monthly", headers=analyst_auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data["monthly_data"]) == 1
        assert data["monthly_data"][0]["income"] == 1000
        assert data["monthly_data"][0]["expenses"] == 200
        assert data["monthly_data"][0]["net"] == 800


class TestRecentActivity:
    """Tests for recent activity endpoint."""
    
    def test_recent_activity_empty(self, client, auth_headers):
        """Test recent activity with no transactions."""
        response = client.get("/api/summaries/recent", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["transactions"] == []
    
    def test_recent_activity_with_data(self, client, analyst_auth_headers):
        """Test recent activity with transactions."""
        # Create recent transactions
        for i in range(5):
            client.post(
                "/api/transactions",
                json={
                    "amount": 100,
                    "type": "income",
                    "category": "Test",
                    "date": str(date.today() - timedelta(days=i))
                },
                headers=analyst_auth_headers
            )
        
        response = client.get("/api/summaries/recent?days=7&limit=3", headers=analyst_auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data["transactions"]) == 3
        assert data["days"] == 7


class TestExport:
    """Tests for export endpoint."""
    
    def test_export_json(self, client, analyst_auth_headers):
        """Test JSON export."""
        # Create transaction
        client.post(
            "/api/transactions",
            json={
                "amount": 100,
                "type": "income",
                "category": "Test",
                "date": str(date.today())
            },
            headers=analyst_auth_headers
        )
        
        response = client.get("/api/summaries/export?format=json", headers=analyst_auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["format"] == "json"
        assert data["record_count"] == 1
    
    def test_export_csv(self, client, analyst_auth_headers):
        """Test CSV export."""
        # Create transaction
        client.post(
            "/api/transactions",
            json={
                "amount": 100,
                "type": "income",
                "category": "Test",
                "date": str(date.today())
            },
            headers=analyst_auth_headers
        )
        
        response = client.get("/api/summaries/export?format=csv", headers=analyst_auth_headers)
        assert response.status_code == 200
        assert "text/csv" in response.headers["content-type"]
