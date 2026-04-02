"""
Tests for transaction endpoints.
"""

from datetime import date, timedelta
from fastapi.testclient import TestClient
from app.models.user import UserRole
from app.models.transaction import TransactionType


class TestTransactionCreate:
    """Tests for transaction creation."""
    
    def test_create_transaction_as_analyst(self, client, analyst_auth_headers):
        """Test creating a transaction as analyst."""
        transaction_data = {
            "amount": 100.50,
            "type": "income",
            "category": "Salary",
            "date": str(date.today()),
            "notes": "Monthly salary"
        }
        response = client.post(
            "/api/transactions",
            json=transaction_data,
            headers=analyst_auth_headers
        )
        assert response.status_code == 201
        data = response.json()
        assert data["amount"] == 100.50
        assert data["type"] == "income"
        assert data["category"] == "Salary"
    
    def test_create_transaction_as_admin(self, client, admin_auth_headers):
        """Test creating a transaction as admin."""
        transaction_data = {
            "amount": 50.00,
            "type": "expense",
            "category": "Food",
            "date": str(date.today())
        }
        response = client.post(
            "/api/transactions",
            json=transaction_data,
            headers=admin_auth_headers
        )
        assert response.status_code == 201
        assert response.json()["type"] == "expense"
    
    def test_create_transaction_as_viewer_forbidden(self, client, auth_headers):
        """Test that viewers cannot create transactions."""
        transaction_data = {
            "amount": 100.00,
            "type": "income",
            "category": "Bonus",
            "date": str(date.today())
        }
        response = client.post(
            "/api/transactions",
            json=transaction_data,
            headers=auth_headers
        )
        assert response.status_code == 403
    
    def test_create_transaction_negative_amount(self, client, analyst_auth_headers):
        """Test that negative amounts are rejected."""
        transaction_data = {
            "amount": -100.00,
            "type": "income",
            "category": "Test",
            "date": str(date.today())
        }
        response = client.post(
            "/api/transactions",
            json=transaction_data,
            headers=analyst_auth_headers
        )
        assert response.status_code == 422
    
    def test_create_transaction_unauthorized(self, client):
        """Test creating transaction without authentication."""
        transaction_data = {
            "amount": 100.00,
            "type": "income",
            "category": "Test",
            "date": str(date.today())
        }
        response = client.post("/api/transactions", json=transaction_data)
        assert response.status_code == 401  # Unauthorized


class TestTransactionList:
    """Tests for transaction listing."""
    
    def test_list_transactions_empty(self, client, auth_headers):
        """Test listing transactions when none exist."""
        response = client.get("/api/transactions", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["transactions"] == []
    
    def test_list_transactions_with_data(self, client, analyst_auth_headers):
        """Test listing transactions with data."""
        # Create some transactions
        for i in range(3):
            client.post(
                "/api/transactions",
                json={
                    "amount": 100 * (i + 1),
                    "type": "income",
                    "category": f"Category{i}",
                    "date": str(date.today() - timedelta(days=i))
                },
                headers=analyst_auth_headers
            )
        
        response = client.get("/api/transactions", headers=analyst_auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 3
        assert len(data["transactions"]) == 3
    
    def test_list_transactions_pagination(self, client, analyst_auth_headers):
        """Test transaction pagination."""
        # Create 25 transactions
        for i in range(25):
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
        
        # Get first page
        response = client.get(
            "/api/transactions?page=1&page_size=10",
            headers=analyst_auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["transactions"]) == 10
        assert data["total_pages"] == 3
    
    def test_list_transactions_filter_by_type(self, client, analyst_auth_headers):
        """Test filtering transactions by type."""
        # Create income and expense
        client.post(
            "/api/transactions",
            json={
                "amount": 100,
                "type": "income",
                "category": "Salary",
                "date": str(date.today())
            },
            headers=analyst_auth_headers
        )
        client.post(
            "/api/transactions",
            json={
                "amount": 50,
                "type": "expense",
                "category": "Food",
                "date": str(date.today())
            },
            headers=analyst_auth_headers
        )
        
        # Filter by income
        response = client.get(
            "/api/transactions?type=income",
            headers=analyst_auth_headers
        )
        data = response.json()
        assert data["total"] == 1
        assert data["transactions"][0]["type"] == "income"


class TestTransactionUpdate:
    """Tests for transaction updates."""
    
    def test_update_transaction(self, client, analyst_auth_headers):
        """Test updating a transaction."""
        # Create transaction
        create_response = client.post(
            "/api/transactions",
            json={
                "amount": 100,
                "type": "income",
                "category": "Salary",
                "date": str(date.today())
            },
            headers=analyst_auth_headers
        )
        transaction_id = create_response.json()["id"]
        
        # Update transaction
        update_response = client.put(
            f"/api/transactions/{transaction_id}",
            json={"amount": 150, "notes": "Updated amount"},
            headers=analyst_auth_headers
        )
        assert update_response.status_code == 200
        data = update_response.json()
        assert data["amount"] == 150
    
    def test_update_nonexistent_transaction(self, client, analyst_auth_headers):
        """Test updating a non-existent transaction."""
        response = client.put(
            "/api/transactions/9999",
            json={"amount": 100},
            headers=analyst_auth_headers
        )
        assert response.status_code == 404


class TestTransactionDelete:
    """Tests for transaction deletion."""
    
    def test_delete_transaction_as_admin(self, client, admin_auth_headers):
        """Test deleting a transaction as admin."""
        # Create transaction
        create_response = client.post(
            "/api/transactions",
            json={
                "amount": 100,
                "type": "income",
                "category": "Test",
                "date": str(date.today())
            },
            headers=admin_auth_headers
        )
        transaction_id = create_response.json()["id"]
        
        # Delete transaction
        delete_response = client.delete(
            f"/api/transactions/{transaction_id}",
            headers=admin_auth_headers
        )
        assert delete_response.status_code == 204
    
    def test_delete_transaction_as_analyst_forbidden(self, client, analyst_auth_headers):
        """Test that analysts cannot delete transactions."""
        # Create transaction
        create_response = client.post(
            "/api/transactions",
            json={
                "amount": 100,
                "type": "income",
                "category": "Test",
                "date": str(date.today())
            },
            headers=analyst_auth_headers
        )
        transaction_id = create_response.json()["id"]
        
        # Try to delete
        delete_response = client.delete(
            f"/api/transactions/{transaction_id}",
            headers=analyst_auth_headers
        )
        assert delete_response.status_code == 403
