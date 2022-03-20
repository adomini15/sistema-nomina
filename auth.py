from functools import wraps
from flask import session, redirect, request, make_response, render_template
import jwt


# middleware
def check_auth(fn):

    @wraps(fn)
    def decorated(*args, **kwargs):
        try:
            token = request.cookies.get('jwt')

            if token:
                payload = jwt.decode(token, 'YouNeverBeAbleToDestroyMe', 'HS256')  # noqa: E501

                if payload:
                    return fn(*args, **kwargs)

            raise jwt.exceptions.DecodeError

        except (jwt.exceptions.ExpiredSignatureError, jwt.exceptions.DecodeError):  # noqa: E501
            res = make_response(render_template('login.html'))

            res.status_code = 401

            return res

    return decorated
