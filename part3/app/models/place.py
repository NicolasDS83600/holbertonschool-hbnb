from app import db
from .base import BaseModel
 
 
place_amenity = db.Table(
    'place_amenity',
    db.Column('place_id', db.String(36), db.ForeignKey('places.id'), primary_key=True),
    db.Column('amenity_id', db.String(36), db.ForeignKey('amenities.id'), primary_key=True)
)
 
 
class Place(BaseModel):
    __tablename__ = 'places'
 
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True, default="")
    price = db.Column(db.Float, nullable=False)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    owner_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
 
    owner = db.relationship('User', backref=db.backref('places', lazy=True), foreign_keys=[owner_id])
    reviews = db.relationship('Review', backref=db.backref('place', lazy=True), lazy=True)
    amenities = db.relationship('Amenity', secondary=place_amenity,
                                lazy='subquery', backref=db.backref('places', lazy=True))
 
    def __init__(
        self,
        title: str,
        description: str,
        price: float,
        latitude: float,
        longitude: float,
        owner_id: str,
    ):
        super().__init__()
        self.title = self._validate_title(title)
        self.description = description or ""
        self.price = self._validate_price(price)
        self.latitude = self._validate_latitude(latitude)
        self.longitude = self._validate_longitude(longitude)
        self.owner_id = owner_id
 
    @staticmethod
    def _validate_title(value: str) -> str:
        if not isinstance(value, str) or not value.strip():
            raise ValueError("title is required")
        value = value.strip()
        if len(value) > 100:
            raise ValueError("title must be <= 100 characters")
        return value
 
    @staticmethod
    def _validate_price(value) -> float:
        if not isinstance(value, (int, float)):
            raise ValueError("price must be a number")
        value = float(value)
        if value <= 0:
            raise ValueError("price must be a positive value")
        return value
 
    @staticmethod
    def _validate_latitude(value) -> float:
        if not isinstance(value, (int, float)):
            raise ValueError("latitude must be a number")
        value = float(value)
        if value < -90.0 or value > 90.0:
            raise ValueError("latitude must be between -90 and 90")
        return value
 
    @staticmethod
    def _validate_longitude(value) -> float:
        if not isinstance(value, (int, float)):
            raise ValueError("longitude must be a number")
        value = float(value)
        if value < -180.0 or value > 180.0:
            raise ValueError("longitude must be between -180 and 180")
        return value
 
    def add_amenity(self, amenity):
        if amenity not in self.amenities:
            self.amenities.append(amenity)
 
    def update(self, data: dict):
        if "title" in data:
            self.title = self._validate_title(data["title"])
        if "description" in data:
            self.description = data["description"] or ""
        if "price" in data:
            self.price = self._validate_price(data["price"])
        if "latitude" in data:
            self.latitude = self._validate_latitude(data["latitude"])
        if "longitude" in data:
            self.longitude = self._validate_longitude(data["longitude"])
        self.save()
 