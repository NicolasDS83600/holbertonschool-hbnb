from flask_restx import Namespace, Resource, fields
from flask_jwt_extended import create_access_token
from ...services import facade

api = Namespace("auth", description="Authentication operations")

login_model = api.model("Login", {
    "email": fields.String(required=True, description="User email"),
    "password": fields.String(required=True, description="User password")
})


@api.route("/login")
class Login(Resource):
    @api.expect(login_model, validate=True)
    def post(self):
        """Authenticate a user and return a JWT access token"""
        data = api.payload

        email = data.get("email")
        password = data.get("password")

        user = facade.authenticate_user(email, password)
        if not user:
            api.abort(401, "Invalid email or password")

        access_token = create_access_token(
            identity=user["id"],
            additional_claims={"is_admin": user["is_admin"]}
        )

        return {"access_token": access_token}, 200