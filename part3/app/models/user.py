import re
from app import db, bcrypt
from .base import BaseModel

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class User(BaseModel):
    __tablename__ = 'users'

    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(120), nullable=False, unique=True)
    password = db.Column(db.String(128), nullable=False)
    is_admin = db.Column(db.Boolean, default=False, nullable=False)

    def __init__(
        self,
        first_name: str,
        last_name: str,
        email: str,
        password: str,
        is_admin: bool = False
    ):
        super().__init__()
        self.first_name = self._validate_name(first_name, "first_name", 50)
        self.last_name = self._validate_name(last_name,  "last_name",  50)
        self.email = self._validate_email(email)
        self.is_admin = bool(is_admin)
        self.hash_password(password)

    @staticmethod
    def _validate_name(value: str, field: str, max_len: int) -> str:
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{field} is required")
        value = value.strip()
        if len(value) > max_len:
            raise ValueError(f"{field} must be <= {max_len} characters")
        return value

    @staticmethod
    def _validate_email(value: str) -> str:
        if not isinstance(value, str) or not value.strip():
            raise ValueError("email is required")
        value = value.strip().lower()
        if not EMAIL_RE.match(value):
            raise ValueError("email format is invalid")
        return value

    def hash_password(self, password: str) -> None:
        """Hash the password and store it."""
        if not isinstance(password, str) or not password.strip():
            raise ValueError("password is required")
        self.password = bcrypt.generate_password_hash(
            password.strip()
        ).decode("utf-8")

    def verify_password(self, password: str) -> bool:
        if not isinstance(password, str):
            return False
        return bcrypt.check_password_hash(self.password, password)

    def update(self, data: dict):
        """Update user fields with validation."""
        if "first_name" in data:
            self.first_name = self._validate_name(data["first_name"], "first_name", 50)
        if "last_name" in data:
            self.last_name = self._validate_name(data["last_name"], "last_name", 50)
        if "email" in data:
            self.email = self._validate_email(data["email"])
        if "is_admin" in data:
            self.is_admin = bool(data["is_admin"])
        if "password" in data:
            self.hash_password(data["password"])
        self.save()

    def to_dict(self) -> dict:
        """Return a dictionary representation without the password."""
        return {
            "id": self.id,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "email": self.email,
            "is_admin": self.is_admin,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }