from flask_restx import Namespace, Resource, fields
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
    "is_admin": fields.Boolean(required=False),
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

    @api.expect(user_create_model, validate=True)
    @api.marshal_with(user_model, code=201)
    def post(self):
        """Create a new user"""
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

    @api.expect(user_update_model, validate=True)
    @api.marshal_with(user_model)
    def put(self, user_id):
        """Update a user"""
        try:
            updated = facade.update_user(user_id, api.payload)
            if not updated:
                api.abort(404, "User not found")
            return updated, 200
        except (ValueError, TypeError) as e:
            api.abort(400, str(e))