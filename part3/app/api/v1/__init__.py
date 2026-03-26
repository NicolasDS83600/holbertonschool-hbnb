"""
Package for API version 1 (v1) endpoints.
This module imports all v1 namespaces and exposes them for registration
with the main Flask-RESTx Api instance.
"""

from .auth import api as auth_ns
from .users import api as users_ns
from .places import api as places_ns
from .reviews import api as reviews_ns
from .amenities import api as amenities_ns

namespaces = [
    auth_ns,
    users_ns,
    places_ns,
    reviews_ns,
    amenities_ns
    ]
