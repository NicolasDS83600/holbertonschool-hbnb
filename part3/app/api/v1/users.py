from flask_restx import Namespace, Resource, fields
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from ...services import facade
 
api = Namespace("users", description="User operations")
 
user_model = api.model("User", {
    "id": fields.String(readonly=True),
    "first_name": fields.String(required=True),
    "last_name": fields.String(required=True),
    "email": fields.String(required=True),
    "is_admin": fields.Boolean(required=False),
    "created_at": fields.String(readonly=True),
    "updated_at": fields.String(readonly=True),
})
 
user_create_model = api.model("UserCreate", {
    "first_name": fields.String(required=True),
    "last_name": fields.String(required=True),
    "email": fields.String(required=True),
    "password": fields.String(required=True),
    "is_admin": fields.Boolean(required=False),
})
 
user_update_model = api.model("UserUpdate", {
    "first_name": fields.String(required=False),
    "last_name": fields.String(required=False),
    "email": fields.String(required=False),
    "password": fields.String(required=False),
})
 
# Parser for query params
user_query_parser = api.parser()
user_query_parser.add_argument(
    "email",
    type=str,
    required=False,
    help="Search user by email",
)
 
 
@api.route("/")
class UserList(Resource):
 
    @api.expect(user_query_parser)
    @api.marshal_list_with(user_model)
    def get(self):
        """Get all users"""
        args = user_query_parser.parse_args()
        email = args.get("email")
 
        if email:
            user = facade.get_user_by_email(email)
            if not user:
                api.abort(404, "User not found")
            return [user]
 
        return facade.get_all_users()
 
    @jwt_required()
    @api.expect(user_create_model, validate=True)
    @api.marshal_with(user_model, code=201)
    def post(self):
        """Create a new user — admin only"""
        claims = get_jwt()
        if not claims.get("is_admin"):
            api.abort(403, "Admin privileges required")
 
        email = api.payload.get("email")
        if facade.get_user_by_email(email):
            api.abort(400, "Email already registered")
 
        try:
            return facade.create_user(api.payload), 201
        except ValueError as e:
            api.abort(400, str(e))
 
 
@api.route("/<string:user_id>")
class UserDetail(Resource):
 
    @api.marshal_with(user_model)
    def get(self, user_id):
        """Get a user by id"""
        try:
            user = facade.get_user(user_id)
            if not user:
                api.abort(404, "User not found")
            return user
        except ValueError as e:
            api.abort(404, str(e))
 
    @jwt_required()
    @api.expect(user_update_model, validate=True)
    @api.marshal_with(user_model)
    def put(self, user_id):
        """Update a user"""
        current_user_id = get_jwt_identity()
        claims = get_jwt()
        is_admin = claims.get("is_admin", False)
 
        if is_admin:
            data = api.payload
            email = data.get("email")
            if email:
                existing = facade.get_user_by_email(email)
                if existing and existing["id"] != user_id:
                    api.abort(400, "Email is already in use")
            try:
                updated = facade.admin_update_user(user_id, data)
                if not updated:
                    api.abort(404, "User not found")
                return updated, 200
            except ValueError as e:
                api.abort(400, str(e))
        else:
            if current_user_id != user_id:
                api.abort(403, "You can only modify your own user")
 
            payload = api.payload
            if "email" in payload or "password" in payload:
                api.abort(400, "You cannot modify email or password")
 
            try:
                updated = facade.update_user(user_id, payload)
                if not updated:
                    api.abort(404, "User not found")
                return updated, 200
            except (ValueError, TypeError) as e:
                api.abort(400, str(e))