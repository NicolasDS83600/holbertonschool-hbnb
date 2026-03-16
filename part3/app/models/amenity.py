from app import db
from .base import BaseModel


class Amenity(BaseModel):
    __tablename__ = 'amenities'

    name = db.Column(db.String(50), nullable=False, unique=True)

    def __init__(self, name: str):
        super().__init__()
        self.name = self._validate_name(name)

    @staticmethod
    def _validate_name(value: str) -> str:
        if not isinstance(value, str) or not value.strip():
            raise ValueError("name is required")
        value = value.strip()
        if len(value) > 50:
            raise ValueError("name must be <= 50 characters")
        return value

    def update(self, data: dict):
        if "name" in data:
            self.name = self._validate_name(data["name"])
        self.save()
