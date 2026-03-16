from app import db
from .base import BaseModel


class Review(BaseModel):
    __tablename__ = 'reviews'

    text    = db.Column(db.Text, nullable=False)
    rating  = db.Column(db.Integer, nullable=False)
    user_id  = db.Column(db.String(36), db.ForeignKey('users.id'),  nullable=False)
    place_id = db.Column(db.String(36), db.ForeignKey('places.id'), nullable=False)

    def __init__(self, text: str, rating: int, place, user):
        super().__init__()
        self.text     = self._validate_text(text)
        self.rating   = self._validate_rating(rating)
        self.place_id = place.id
        self.user_id  = user.id

        self._place = place
        self._user  = user

    @staticmethod
    def _validate_text(value: str) -> str:
        if not isinstance(value, str) or not value.strip():
            raise ValueError("text is required")
        return value.strip()

    @staticmethod
    def _validate_rating(value: int) -> int:
        if not isinstance(value, int):
            raise ValueError("rating must be an integer")
        if value < 1 or value > 5:
            raise ValueError("rating must be between 1 and 5")
        return value

    @property
    def place(self):
        return self._place

    @property
    def user(self):
        return self._user

    def update(self, data: dict):
        if "text" in data:
            self.text = self._validate_text(data["text"])
        if "rating" in data:
            self.rating = self._validate_rating(data["rating"])
        self.save()