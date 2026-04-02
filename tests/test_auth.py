"""
Tests for authentication endpoints.
"""

from fastapi.testclient import TestClient
from app.models.user import UserRole


class TestUserRegistration:
    """Tests for user registration."""
    
    def test_register_success(self, client):
        """Test successful user registration."""
        user_data = {
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "password123"
        }
        response = client.post("/api/auth/register", json=user_data)
        assert response.status_code == 201
        data = response.json()
        assert data["username"] == "newuser"
        assert data["email"] == "newuser@example.com"
        assert data["role"] == "viewer"
        assert "password" not in data
    
    def test_register_duplicate_username(self, client, test_user):
        """Test registration with duplicate username."""
        user_data = {
            "username": "testuser",  # Already exists
            "email": "different@example.com",
            "password": "password123"
        }
        response = client.post("/api/auth/register", json=user_data)
        assert response.status_code == 400
        assert "Username already registered" in response.json()["detail"]
    
    def test_register_duplicate_email(self, client, test_user):
        """Test registration with duplicate email."""
        user_data = {
            "username": "different",
            "email": "test@example.com",  # Already exists
            "password": "password123"
        }
        response = client.post("/api/auth/register", json=user_data)
        assert response.status_code == 400
        assert "Email already registered" in response.json()["detail"]
    
    def test_register_short_password(self, client):
        """Test registration with too short password."""
        user_data = {
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "short"
        }
        response = client.post("/api/auth/register", json=user_data)
        assert response.status_code == 422
    
    def test_register_invalid_email(self, client):
        """Test registration with invalid email."""
        user_data = {
            "username": "newuser",
            "email": "notanemail",
            "password": "password123"
        }
        response = client.post("/api/auth/register", json=user_data)
        assert response.status_code == 422
    
    def test_register_password_no_number(self, client):
        """Test registration with password without numbers."""
        user_data = {
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "passwordonly"
        }
        response = client.post("/api/auth/register", json=user_data)
        assert response.status_code == 422


class TestUserLogin:
    """Tests for user login."""
    
    def test_login_success(self, client, test_user):
        """Test successful login."""
        login_data = {
            "username": "testuser",
            "password": "test123"
        }
        response = client.post("/api/auth/login", json=login_data)
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert "user" in data
    
    def test_login_wrong_password(self, client, test_user):
        """Test login with wrong password."""
        login_data = {
            "username": "testuser",
            "password": "wrongpassword"
        }
        response = client.post("/api/auth/login", json=login_data)
        assert response.status_code == 401
    
    def test_login_nonexistent_user(self, client):
        """Test login with non-existent user."""
        login_data = {
            "username": "nonexistent",
            "password": "anypassword"
        }
        response = client.post("/api/auth/login", json=login_data)
        assert response.status_code == 401


class TestGetCurrentUser:
    """Tests for getting current user info."""
    
    def test_get_current_user_success(self, client, auth_headers):
        """Test getting current user info."""
        response = client.get("/api/auth/me", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "testuser"
    
    def test_get_current_user_no_token(self, client):
        """Test getting current user without token."""
        response = client.get("/api/auth/me")
        assert response.status_code == 401  # Unauthorized when no token provided
    
    def test_get_current_user_invalid_token(self, client):
        """Test getting current user with invalid token."""
        headers = {"Authorization": "Bearer invalidtoken"}
        response = client.get("/api/auth/me", headers=headers)
        assert response.status_code == 401


class TestUserRoleAccess:
    """Tests for role-based access control."""
    
    def test_viewer_can_read_transactions(self, client, auth_headers):
        """Test that viewer can read transactions."""
        response = client.get("/api/transactions", headers=auth_headers)
        assert response.status_code == 200
    
    def test_viewer_cannot_create_transactions(self, client, auth_headers):
        """Test that viewer cannot create transactions."""
        transaction_data = {
            "amount": 100,
            "type": "income",
            "category": "Test",
            "date": "2024-01-01"
        }
        response = client.post(
            "/api/transactions",
            json=transaction_data,
            headers=auth_headers
        )
        assert response.status_code == 403
    
    def test_analyst_can_create_transactions(self, client, analyst_auth_headers):
        """Test that analyst can create transactions."""
        transaction_data = {
            "amount": 100,
            "type": "income",
            "category": "Test",
            "date": "2024-01-01"
        }
        response = client.post(
            "/api/transactions",
            json=transaction_data,
            headers=analyst_auth_headers
        )
        assert response.status_code == 201
    
    def test_admin_can_delete_transactions(self, client, admin_auth_headers):
        """Test that admin can delete transactions."""
        # Create a transaction first
        create_response = client.post(
            "/api/transactions",
            json={
                "amount": 100,
                "type": "income",
                "category": "Test",
                "date": "2024-01-01"
            },
            headers=admin_auth_headers
        )
        transaction_id = create_response.json()["id"]
        
        # Delete it
        delete_response = client.delete(
            f"/api/transactions/{transaction_id}",
            headers=admin_auth_headers
        )
        assert delete_response.status_code == 204
