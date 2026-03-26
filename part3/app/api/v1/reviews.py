from flask_restx import Namespace, Resource, fields
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from app.services import facade
 
api = Namespace('reviews', description='Review operations')
 
review_model = api.model('Review', {
    'id': fields.String(readonly=True, description='Review ID'),
    'text': fields.String(required=True, description='Text of the review'),
    'rating': fields.Integer(required=True, description='Rating of the place (1-5)'),
    'user_id': fields.String(description='ID of the user'),
    'place_id': fields.String(required=True, description='ID of the place')
})
 
review_create_model = api.model('ReviewCreate', {
    'text': fields.String(required=True, description='Text of the review'),
    'rating': fields.Integer(required=True, description='Rating of the place (1-5)'),
    'place_id': fields.String(required=True, description='ID of the place')
})
 
review_update_model = api.model('ReviewUpdate', {
    'text': fields.String(required=False, description='Text of the review'),
    'rating': fields.Integer(required=False, description='Rating of the place (1-5)')
})
 
 
@api.route('/')
class ReviewList(Resource):
    @jwt_required()
    @api.expect(review_create_model, validate=True)
    @api.marshal_with(review_model, code=201)
    @api.response(201, 'Review successfully created')
    @api.response(400, 'Invalid input data')
    @api.response(401, 'Authentication required')
    def post(self):
        """Create a new review"""
        data = api.payload
        data["user_id"] = get_jwt_identity()
 
        try:
            new_review = facade.create_review(data)
            return new_review, 201
        except (ValueError, TypeError) as e:
            api.abort(400, str(e))
 
    @api.marshal_list_with(review_model)
    @api.response(200, 'List of reviews retrieved successfully')
    def get(self):
        """Retrieve a list of all reviews"""
        return facade.get_all_reviews(), 200
 
 
@api.route('/<string:review_id>')
class ReviewResource(Resource):
    @api.marshal_with(review_model)
    @api.response(200, 'Review details retrieved successfully')
    @api.response(404, 'Review not found')
    def get(self, review_id):
        """Get a review by id"""
        try:
            review = facade.get_review_by_id(review_id)
            if not review:
                api.abort(404, "Review not found")
            return review, 200
        except ValueError as e:
            api.abort(404, str(e))
 
    @jwt_required()
    @api.expect(review_update_model, validate=True)
    @api.marshal_with(review_model)
    @api.response(200, 'Review updated successfully')
    @api.response(403, 'Forbidden')
    @api.response(404, 'Review not found')
    @api.response(400, 'Invalid input data')
    def put(self, review_id):
        """Update a review"""
        current_user_id = get_jwt_identity()
        claims = get_jwt()
        is_admin = claims.get("is_admin", False)
 
        try:
            review = facade.get_review_by_id(review_id)
        except ValueError:
            api.abort(404, "Review not found")
 
        if not is_admin and review["user_id"] != current_user_id:
            api.abort(403, "Unauthorized action")
 
        try:
            updated_review = facade.update_review(review_id, api.payload)
            if not updated_review:
                api.abort(404, "Review not found")
            return updated_review, 200
        except (ValueError, TypeError) as e:
            api.abort(400, str(e))
 
    @jwt_required()
    @api.response(200, 'Review deleted successfully')
    @api.response(403, 'Forbidden')
    @api.response(404, 'Review not found')
    def delete(self, review_id):
        """Delete a review"""
        current_user_id = get_jwt_identity()
        claims = get_jwt()
        is_admin = claims.get("is_admin", False)
 
        try:
            review = facade.get_review_by_id(review_id)
        except ValueError:
            api.abort(404, "Review not found")
 
        if not is_admin and review["user_id"] != current_user_id:
            api.abort(403, "Unauthorized action")
 
        success = facade.delete_review(review_id)
        if not success:
            api.abort(404, "Review not found")
 
        return {"message": "Review deleted successfully"}, 200