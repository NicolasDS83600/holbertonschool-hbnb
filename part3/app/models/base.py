import uuid
from datetime import datetime
from app import db


class BaseModel(db.Model):
    __abstract__ = True

    id = db.Column(
        db.String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )

    def save(self):
        """Update the updated_at timestamp and commit."""
        self.updated_at = datetime.utcnow()
        db.session.commit()

    def update(self, data: dict):
        """
        Update existing attributes only, then refresh updated_at.
        Child classes may override this for validation.
        """
        for key, value in data.items():
            if hasattr(self, key):
                setattr(self, key, value)
        self.save()