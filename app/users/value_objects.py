# app/core/value_objects.py

import re
from dataclasses import dataclass

# Asumimos que esta es la ruta a tu excepción personalizada
from ..core.exceptions import InvaiidPasswordFormatException


@dataclass(frozen=True)
class PasswordStr:
    v: str
    """
    Valida que la contraseña cumpla con los criterios de seguridad definidos.
    - Al menos 8 caracteres de longitud.
    - Al menos una letra minúscula.
    - Al menos una letra mayúscula.
    - Al menos un dígito.
    - Al menos un carácter especial.
    
    """
    v: str

    def __post_init__(self):
        object.__setattr__(self, 'v', self.validate_password_strength())

    def validate_password_strength(self):
        # 1. Validación de longitud (ser mayor a 8 caracteres, interpretado como >= 8)
        if len(self.v) < 8:
            raise InvaiidPasswordFormatException('must be at least 8 characters long')

        # 2. Validación de minúscula
        if not re.search(r'[a-z]', self.v):
            raise InvaiidPasswordFormatException(
                'must contain at least one lowercase letter'
            )

        # 3. Validación de mayúscula
        if not re.search(r'[A-Z]', self.v):
            raise InvaiidPasswordFormatException(
                'must contain at least one uppercase letter'
            )

        # 4. Validación de número
        if not re.search(r'\d', self.v):
            raise InvaiidPasswordFormatException('must contain at least one digit')

        # 5. Validación de carácter especial
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', self.v):
            raise InvaiidPasswordFormatException(
                'must contain at least one special character'
            )

        return self.v
