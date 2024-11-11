"""
Authorization Test Suite

This test module covers various authorization scenarios:
- User registration
- User login
- Password hashing
- Access control
- Token generation and validation
"""

import pytest
from unittest.mock import patch, MagicMock
from datetime import timedelta

from app.models.user import User
from app.services.auth_service import AuthService
from app.services.token_service import TokenService
from app.exceptions import (
    UserAlreadyExistsError,
    InvalidCredentialsError,
    AuthorizationError
)
from config.security import SecurityConfig

class TestAuthorization:
    @pytest.fixture
    def auth_service(self):
        """
        Fixture to create an AuthService instance for testing
        """
        return AuthService()

    @pytest.fixture
    def token_service(self):
        """
        Fixture to create a TokenService instance for testing
        """
        return TokenService(SecurityConfig())

    def test_user_registration_success(self, auth_service):
        """
        Test successful user registration
        """
        username = "testuser"
        email = "testuser@example.com"
        password = "strongpassword123"

        # Mock database session and query
        with patch('app.services.auth_service.get_session') as mock_get_session:
            mock_session = MagicMock()
            mock_get_session.return_value = mock_session

            # Simulate no existing user
            mock_session.query().filter().first.return_value = None

            # Perform registration
            user = auth_service.register_user(
                username=username,
                email=email,
                password=password
            )

            # Assertions
            assert user.username == username
            assert user.email == email
            assert user.password != password  # Ensure password is hashed
            mock_session.add.assert_called_once()
            mock_session.commit.assert_called_once()

    def test_user_registration_existing_user(self, auth_service):
        """
        Test registration with existing username or email
        """
        username = "existinguser"
        email = "existinguser@example.com"
        password = "strongpassword123"

        # Mock database session and query
        with patch('app.services.auth_service.get_session') as mock_get_session:
            mock_session = MagicMock()
            mock_get_session.return_value = mock_session

            # Simulate existing user
            existing_user = User(
                username=username,
                email=email,
                password="hashedpassword"
            )
            mock_session.query().filter().first.return_value = existing_user

            # Expect UserAlreadyExistsError
            with pytest.raises(UserAlreadyExistsError):
                auth_service.register_user(
                    username=username,
                    email=email,
                    password=password
                )

    def test_user_login_success(self, auth_service, token_service):
        """
        Test successful user login
        """
        username = "loginuser"
        email = "loginuser@example.com"
        password = "correctpassword123"
        hashed_password = auth_service.hash_password(password)

        # Mock database session and query
        with patch('app.services.auth_service.get_session') as mock_get_session:
            mock_session = MagicMock()
            mock_get_session.return_value = mock_session

            # Simulate existing user with correct credentials
            existing_user = User(
                username=username,
                email=email,
                password=hashed_password
            )
            mock_session.query().filter().first.return_value = existing_user

            # Perform login
            token = auth_service.login(
                username=username,
                password=password
            )

            # Assertions
            assert token is not None
            assert token_service.validate_token(token)

    def test_user_login_invalid_credentials(self, auth_service):
        """
        Test login with incorrect credentials
        """
        username = "invaliduser"
        password = "wrongpassword"

        # Mock database session and query
        with patch('app.services.auth_service.get_session') as mock_get_session:
            mock_session = MagicMock()
            mock_get_session.return_value = mock_session

            # Simulate no existing user
            mock_session.query().filter().first.return_value = None

            # Expect InvalidCredentialsError
            with pytest.raises(InvalidCredentialsError):
                auth_service.login(
                    username=username,
                    password=password
                )

    def test_password_reset_flow(self, auth_service, token_service):
        """
        Test password reset workflow
        """
        email = "resetuser@example.com"
        new_password = "newstrongpassword123"

        # Mock database session and query
        with patch('app.services.auth_service.get_session') as mock_get_session:
            mock_session = MagicMock()
            mock_get_session.return_value = mock_session

            # Simulate existing user
            existing_user = User(
                username="resetuser",
                email=email,
                password=auth_service.hash_password("oldpassword")
            )
            mock_session.query().filter().first.return_value = existing_user

            # Generate password reset token
            reset_token = auth_service.generate_password_reset_token(email)
            assert reset_token is not None

            # Validate and reset password
            reset_result = auth_service.reset_password(
                reset_token, 
                new_password
            )
            assert reset_result is True

            # Verify password was updated
            assert auth_service.verify_password(
                new_password, 
                existing_user.password
            )

    def test_token_expiration(self, token_service):
        """
        Test token expiration mechanism
        """
        user = User(
            username="tokenuser",
            email="tokenuser@example.com"
        )

        # Generate token with short expiration
        short_expiry_token = token_service.generate_token(
            user, 
            expires_delta=timedelta(seconds=1)
        )

        # Validate immediately
        assert token_service.validate_token(short_expiry_token)

        # Wait for token to expire
        import time
        time.sleep(2)

        # Token should be invalid after expiration
        with pytest.raises(AuthorizationError):
            token_service.validate_token(short_expiry_token)

    def test_role_based_access_control(self, auth_service):
        """
        Test role-based access control
        """
        admin_user = User(
            username="admin",
            email="admin@example.com",
            role="ADMIN"
        )
        regular_user = User(
            username="user",
            email="user@example.com",
            role="USER"
        )

        # Mock authorization service
        with patch('app.services.auth_service.AuthService.check_user_permission'):
            # Admin should have full access
            auth_service.check_user_permission(admin_user, "ADMIN_RESOURCE")
            
            # Regular user should be restricted
            with pytest.raises(AuthorizationError):
                auth_service.check_user_permission(regular_user, "ADMIN_RESOURCE")

    def test_password_complexity(self, auth_service):
        """
        Test password complexity requirements
        """
        # Test weak passwords
        weak_passwords = [
            "short",
            "123456",
            "password",
            "qwerty"
        ]

        for weak_password in weak_passwords:
            with pytest.raises(ValueError):
                auth_service.validate_password(weak_password)

        # Test strong passwords
        strong_passwords = [
            "StrongP@ssw0rd123!",
            "Secure_Password_2023#",
            "ComplexPass123$"
        ]

        for strong_password in strong_passwords:
            assert auth_service.validate_password(strong_password) is True
