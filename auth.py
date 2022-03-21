from functools import wraps
from flask import session, redirect, request, make_response, render_template
import jwt


# middleware
def check_auth(fn):

    @wraps(fn)
    def decorated(*args, **kwargs):
        try:
            # Lee una cookie que contenga el nombre 'jwt'
            token = request.cookies.get('jwt')

            # verifica que haya contenido en 'token'
            if token:
                # decodifica el contenido en token, comprobando primero de que sea un tipo real,
                # que no haya estado vencido y que haya sido generado por esta aplicación, 
                # por la clave secreta que le hemos colocado como cola.
                payload = jwt.decode(token, 'YouNeverBeAbleToDestroyMe', 'HS256')  # noqa: E501

                # si 'payload' es un valor correcto.
                if payload:

                    # retornamos a la función decorada.
                    return fn(*args, **kwargs)

            raise jwt.exceptions.DecodeError

        # captura la excepciones de expiracion o falsificacion de token
        except (jwt.exceptions.ExpiredSignatureError, jwt.exceptions.DecodeError):  # noqa: E501
            res = make_response(render_template('login.html'))

            res.status_code = 401

            return res

    return decorated
