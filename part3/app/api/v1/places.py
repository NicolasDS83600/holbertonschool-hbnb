from flask_restx import Namespace, Resource, fields
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from app.services import facade
 
api = Namespace('places', description='Place operations')
 
amenity_model = api.model('PlaceAmenity', {
    'id': fields.String(description='Amenity ID'),
    'name': fields.String(description='Name of the amenity')
})
 
user_model = api.model('PlaceUser', {
    'id': fields.String(description='User ID'),
    'first_name': fields.String(description='First name of the owner'),
    'last_name': fields.String(description='Last name of the owner'),
    'email': fields.String(description='Email of the owner')
})
 
place_response_model = api.model('PlaceResponse', {
    'id': fields.String(readonly=True, description='Place ID'),
    'title': fields.String(required=True, description='Title of the place'),
    'description': fields.String(description='Description of the place'),
    'price': fields.Float(required=True, description='Price per night'),
    'latitude': fields.Float(required=True, description='Latitude of the place'),
    'longitude': fields.Float(required=True, description='Longitude of the place'),
    'owner_id': fields.String(description='ID of the owner'),
    'amenities': fields.List(fields.String, description="List of amenities IDs")
})
 
place_create_model = api.model('PlaceCreate', {
    'title': fields.String(required=True, description='Title of the place'),
    'description': fields.String(description='Description of the place'),
    'price': fields.Float(required=True, description='Price per night'),
    'latitude': fields.Float(required=True, description='Latitude of the place'),
    'longitude': fields.Float(required=True, description='Longitude of the place'),
    'amenities': fields.List(fields.String, required=False, description="List of amenities IDs")
})
 
place_update_model = api.model('PlaceUpdate', {
    'title': fields.String(required=False, description='Title of the place'),
    'description': fields.String(required=False, description='Description of the place'),
    'price': fields.Float(required=False, description='Price per night'),
    'latitude': fields.Float(required=False, description='Latitude of the place'),
    'longitude': fields.Float(required=False, description='Longitude of the place'),
    'amenities': fields.List(fields.String, required=False, description="List of amenities IDs")
})
 
 
@api.route('/')
class PlaceList(Resource):
    @jwt_required()
    @api.expect(place_create_model, validate=True)
    @api.marshal_with(place_response_model, code=201)
    @api.response(201, 'Place successfully created')
    @api.response(400, 'Invalid input data')
    @api.response(401, 'Authentication required')
    def post(self):
        """Create a new place"""
        place_data = api.payload
        place_data["owner_id"] = get_jwt_identity()
 
        try:
            result = facade.create_place(place_data)
            return result, 201
        except ValueError as e:
            api.abort(400, str(e))
 
    @api.marshal_list_with(place_response_model)
    @api.response(200, 'List of places retrieved successfully')
    def get(self):
        """Retrieve a list of all places"""
        return facade.get_all_places(), 200
 
 
@api.route('/<string:place_id>')
class PlaceResource(Resource):
    @api.marshal_with(place_response_model)
    @api.response(200, 'Place details retrieved successfully')
    @api.response(404, 'Place not found')
    def get(self, place_id):
        """Get place details by ID"""
        try:
            return facade.get_place(place_id), 200
        except ValueError:
            api.abort(404, "Place not found")
 
    @jwt_required()
    @api.expect(place_update_model, validate=True)
    @api.response(200, 'Place updated successfully')
    @api.response(403, 'Forbidden')
    @api.response(404, 'Place not found')
    @api.response(400, 'Invalid input data')
    def put(self, place_id):
        """Update a place"""
        current_user_id = get_jwt_identity()
        claims = get_jwt()
        is_admin = claims.get("is_admin", False)
 
        try:
            place = facade.get_place(place_id)
        except ValueError:
            api.abort(404, "Place not found")
 
        owner_id = place.get("owner_id")
        if not owner_id and "owner" in place:
            owner_id = place["owner"]["id"]
 
        if not is_admin and owner_id != current_user_id:
            api.abort(403, "Unauthorized action")
 
        try:
            result = facade.update_place(place_id, api.payload)
            if result is None:
                api.abort(404, "Place not found")
            return result, 200
        except ValueError as e:
            api.abort(400, str(e))