from flask_restx import Namespace, Resource, fields
from flask_jwt_extended import jwt_required, get_jwt
from app.services import facade
 
api = Namespace('amenities', description='Amenity operations')
 
amenity_model = api.model('Amenity', {
    'id': fields.String(readonly=True),
    'name': fields.String(required=True, description='Name of the amenity')
})
 
amenity_create_model = api.model('AmenityCreate', {
    'name': fields.String(required=True, description='Name of the amenity')
})
 
 
@api.route('/')
class AmenityList(Resource):
 
    @jwt_required()
    @api.expect(amenity_create_model, validate=True)
    @api.response(201, 'Amenity successfully created')
    @api.response(400, 'Invalid input data')
    @api.response(403, 'Admin privileges required')
    def post(self):
        """Register a new amenity — admin only"""
        claims = get_jwt()
        if not claims.get("is_admin"):
            api.abort(403, "Admin privileges required")
 
        try:
            amenity = facade.create_amenity(api.payload)
            return {"id": amenity["id"], "name": amenity["name"]}, 201
        except ValueError as e:
            api.abort(400, str(e))
 
    @api.response(200, 'List of amenities retrieved successfully')
    def get(self):
        """Retrieve a list of all amenities"""
        return facade.get_all_amenities(), 200
 
 
@api.route('/<amenity_id>')
class AmenityResource(Resource):
 
    @api.response(200, 'Amenity details retrieved successfully')
    @api.response(404, 'Amenity not found')
    def get(self, amenity_id):
        """Get amenity details by ID"""
        try:
            return facade.get_amenity(amenity_id), 200
        except ValueError:
            return {"error": "Amenity not found"}, 404
 
    @jwt_required()
    @api.expect(amenity_create_model, validate=True)
    @api.response(200, 'Amenity updated successfully')
    @api.response(400, 'Invalid input data')
    @api.response(403, 'Admin privileges required')
    @api.response(404, 'Amenity not found')
    def put(self, amenity_id):
        """Update an amenity's information — admin only"""
        claims = get_jwt()
        if not claims.get("is_admin"):
            api.abort(403, "Admin privileges required")
 
        try:
            amenity = facade.update_amenity(amenity_id, api.payload)
            if not amenity:
                return {"error": "Amenity not found"}, 404
            return {"message": "Amenity updated successfully"}, 200
        except ValueError as e:
            api.abort(400, str(e))
