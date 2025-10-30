"""
Value objects for user module.

This module defines value objects for user-related domain logic,
specifically password validation with comprehensive security requirements.
"""

import re

from pydantic import GetCoreSchemaHandler
from pydantic_core import core_schema

from ..core.exceptions import InvalidPasswordFormatException


class Password(str):
    """
    Password value object with comprehensive validation.

    This is a Pydantic-compatible value object that validates password strength
    according to security requirements. It inherits from str to work seamlessly
    with Pydantic and FastAPI.

    Requirements (aligned with frontend validation):
    - At least 10 characters long (enhanced from 8 for better security)
    - At least one lowercase letter
    - At least one uppercase letter
    - At least one digit
    - At least one special character
    - Not a common weak password

    Usage in Pydantic schemas:
        from app.users.value_objects import Password

        class UserCreate(BaseModel):
            password: Password  # Automatically validated

    The password will be validated when the Pydantic model is instantiated,
    and validation errors will be properly serialized to JSON with clear messages.
    """

    # List of common weak passwords to reject
    COMMON_WEAK_PASSWORDS = {
        'password',
        'password123',
        '12345678',
        'qwerty',
        'abc123',
        'password1',
        '123456789',
        'admin123',
        'letmein',
        'welcome',
        'monkey',
        'dragon',
        'master',
        'sunshine',
        'princess',
        'football',
        'baseball',
        'superman',
    }

    @classmethod
    def validate(cls, value: str) -> 'Password':
        """
        Validate password strength and return Password instance.

        Args:
            value: The password string to validate

        Returns:
            Password: Validated password instance

        Raises:
            InvalidPasswordFormatException: If password doesn't meet requirements
        """
        if not isinstance(value, str):
            raise InvalidPasswordFormatException('Password must be a string')

        # 1. Length validation (enhanced to 10 characters for better security)
        if len(value) < 10:
            raise InvalidPasswordFormatException(
                'Password must be at least 10 characters long'
            )

        # 2. Lowercase letter validation
        if not re.search(r'[a-z]', value):
            raise InvalidPasswordFormatException(
                'Password must contain at least one lowercase letter'
            )

        # 3. Uppercase letter validation
        if not re.search(r'[A-Z]', value):
            raise InvalidPasswordFormatException(
                'Password must contain at least one uppercase letter'
            )

        # 4. Digit validation
        if not re.search(r'\d', value):
            raise InvalidPasswordFormatException(
                'Password must contain at least one digit'
            )

        # 5. Special character validation
        # Includes common special characters
        if not re.search(r'[!@#$%^&*(),.?":{}|<>_\-+=\[\]\\\/;\'`~]', value):
            raise InvalidPasswordFormatException(
                'Password must contain at least one special character (!@#$%^&*(),.?":{}|<>_-+=[]\\\/;\'`~)'
            )

        # 6. Common password validation
        if value.lower() in cls.COMMON_WEAK_PASSWORDS:
            raise InvalidPasswordFormatException(
                'Password is too common and easily guessable. Please choose a stronger password'
            )

        # Return Password instance (which is a str subclass)
        return cls(value)

    @classmethod
    def __get_pydantic_core_schema__(
        cls, source_type: type, handler: GetCoreSchemaHandler
    ) -> core_schema.CoreSchema:
        """
        Pydantic v2 core schema for Password validation.

        This method tells Pydantic how to validate and serialize Password objects.
        It ensures proper JSON serialization and clear error messages.
        """
        return core_schema.with_info_plain_validator_function(
            cls._validate,
            serialization=core_schema.plain_serializer_function_ser_schema(
                lambda instance: str(instance),
                return_schema=core_schema.str_schema(),
            ),
        )

    @classmethod
    def _validate(cls, value: str, _info) -> 'Password':
        """
        Internal validation method for Pydantic.

        This method is called by Pydantic during model validation.
        It wraps the validate() method and ensures proper error handling.
        """
        return cls.validate(value)

    def __repr__(self) -> str:
        """String representation (hides actual password value)."""
        return 'Password(***)'

    def __str__(self) -> str:
        """Return the actual password value as string."""
        return super().__str__()
