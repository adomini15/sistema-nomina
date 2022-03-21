from flask import Flask, render_template, request, redirect, make_response, jsonify
from DBcm import UseDatabase
from mysql.connector import Error, errors
import simplejson as json
from auth import check_auth
from datetime import datetime, timedelta
import jwt
import re
import bcrypt

# objeto de aplicacion
app = Flask(__name__)

# cadena de conexion de la base de datos
app.config['dbconfig'] = {
    'host': 'localhost',
    'username': 'odil',
    'passwd': '123456',
    'db': 'SISTEMA_NOMINA'
}

# clave secreta utiliza por jwt
app.config['SECRET_KEY'] = 'YouNeverBeAbleToDestroyMe'

# diccionario de errores personalizados
custom_errors = {
    '23000': 'Dato existente.'
}


# ruta encargada de la validar las credenciales del usuario
@app.route('/auth', methods=['POST'])
def authentication():
    try:
        with UseDatabase(app.config['dbconfig']) as cursor:
            # Buscamos a un usuario que se identifique con el siguiente nombre,
            # y si existe, solo recuperamos su id y contrasena.
            _SQL = "SELECT id, contrasena FROM USUARIO WHERE nombre=%s"

            # realizamos la consulta en la base de datos.
            cursor.execute(_SQL, (request.form['nombre'],))

            # obtenemos clave encriptada del usuario que fue encontrado.
            result = cursor.fetchone()

            # condicion que se cumple si no hubo usuario con el nombre buscado, por lo tanto,
            # no fue recuperada ninguna contrasena
            if not result:
                res = make_response(jsonify({
                    'error': {'message': 'Nombre incorrecto.', 'path': 'nombre'}
                }))

                res.status_code = 404

                return res

            # recuperamos el id de la lista de resultado de las columnas solicitadas
            id = result[0]

            # recuperamos la contrasena de la lista de resultado de las columnas solicitadas
            # Cambiamos su codificacion a utf8
            hashed_passwd = result[1].encode('utf8')

            # comparamos la contrasena ya encriptada en la bd con la que viene en la petición.
            if not bcrypt.checkpw(request.form['contrasena'].encode('utf8'), hashed_passwd):  # noqa: E501
                res = make_response(jsonify({
                    'error': {'message': 'Contrasena incorrecta.', 'path': 'contrasena'}  # noqa: E501
                }))

                res.status_code = 404

                return res

            token = jwt.encode({
                'id': id, 'exp': datetime.utcnow() + timedelta(weeks=1)
                }, app.config['SECRET_KEY'])

            res = make_response(jsonify({
                'data': {'message': 'Usuario autenticado.'}
            }))

            res.set_cookie('jwt', token)

            res.status_code = 200

            return res

    except Error as e:
        field = re.search("\.(.*)'", e.msg).group(1)  # noqa: W605

        if e.sqlstate in custom_errors:
            message = custom_errors[e.sqlstate]
        else:
            message = e.msg

        res = make_response(jsonify({'error': {
                    'message': message,
                    'path': field,
                    'sqlcode': e.sqlstate
                }
            })
        )

        res.status_code = 400

        return res


# renderiza la pagina de login
@app.route('/signin')
def signin():
    return render_template('login.html')


# renderiza la pagina para crear cuenta de usuario
@app.route('/signup')
def usuario_create():
    return render_template('usuario.create.html')


# ruta utilizada para procesar creación de nuevo usuario.
@app.route('/usuarios', methods=['POST'])
def usuario_add():
    try:
        with UseDatabase(app.config['dbconfig']) as cursor:
            # encriptamos contrasena del usuario mediante función hash bcrypt
            passwd_hash = bcrypt.hashpw(request.form['contrasena'].encode('utf8'), bcrypt.gensalt())  # noqa: E501

            _SQL = "INSERT INTO USUARIO(nombre, contrasena) VALUES (%s, %s)"
            cursor.execute(_SQL, (request.form['nombre'], passwd_hash))  # noqa: E501

        res = make_response(
                jsonify({'data': {'message': 'Usuario creado satisfactoriamente.'}})  # noqa: E501
                )
        res.status_code = 201

        return res

    except Error as e:
        field = re.search("\.(.*)'", e.msg).group(1)  # noqa: W605

        if e.sqlstate in custom_errors:
            message = custom_errors[e.sqlstate]
        else:
            message = e.msg

        res = make_response(jsonify({'error': {
                    'message': message,
                    'path': field,
                    'sqlcode': e.sqlstate
                }
            })
        )

        res.status_code = 400

        return res


# renderiza la pagina con la lista de empleados.
@app.route('/', methods=['GET'])
@app.route('/empleados', methods=['GET'])
@check_auth
def index():

    with UseDatabase(app.config['dbconfig']) as cursor:
        # creamos una consulta para leer todos los empleados en la base de datos
        cursor.execute('select * from EMPLEADO')

        # despues de que termina de procesar, leemos los datos recuperamos y 
        # lo guardamos en la variable 'empleados'
        empleados = cursor.fetchall()

    # renderizamos la pagina 'index.html', enviando como parte de la capacidad de
    # jinja la variables 'empleados' y 'colums', leidas despues dentro el documento.
    return render_template(
        'index.html', empleados=empleados, columns=cursor.column_names
        )


# ruta utilizada para procesar los datos enviados
# desde el formulario de creación de empleado.
@app.route('/empleados', methods=['POST'])
@check_auth
def empleado_add():
    try:
        with UseDatabase(app.config['dbconfig']) as cursor:
            _SQL = """
                INSERT INTO EMPLEADO
                (nombre,
                estado_civil, sueldo_bruto, ars, afp, isr, sueldo_neto)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(
                _SQL,
                (
                    request.form['nombre'],
                    request.form['estado_civil'],
                    request.form['sueldo_bruto'],
                    request.form['ars'],
                    request.form['afp'],
                    request.form['isr'],
                    request.form['sueldo_neto']
                )
            )

    except Error as e:
        field = re.search("\.(.*)'", e.msg).group(1)  # noqa: W605

        if e.sqlstate in custom_errors:
            message = custom_errors[e.sqlstate]
        else:
            message = e.msg

        res = make_response(jsonify({'error': {
                    'message': message,
                    'path': field,
                    'sqlcode': e.sqlstate
                }
            })
        )

        res.status_code = 400

        return res


# renderizamos la pagina con el formulario de
# creación de empleado.
@app.route('/empleados/create')
@check_auth
def empleado_create():
    return render_template('empleado.create.html')


# ruta que actualiza los datos enviados desde 
# el formulario de actualización de empleado.
@app.route('/empleados/<id>', methods=['PUT'])
@check_auth
def empleado_update(id=0):
    try:
        with UseDatabase(app.config['dbconfig']) as cursor:
            _SQL = """
                UPDATE EMPLEADO SET nombre=%s, estado_civil=%s,
                sueldo_bruto=%s, ars=%s, afp=%s, isr=%s, sueldo_neto=%s
                WHERE id=%s
            """

            cursor.execute(_SQL, (
                    request.form['nombre'],
                    request.form['estado_civil'],
                    request.form['sueldo_bruto'],
                    request.form['ars'],
                    request.form['afp'],
                    request.form['isr'],
                    request.form['sueldo_neto'],
                    id
            ))

    except Error as e:
        field = re.search("\.(.*)'", e.msg).group(1)  # noqa: W605

        if e.sqlstate in custom_errors:
            message = custom_errors[e.sqlstate]
        else:
            message = e.msg

        res = make_response(jsonify({'error': {
                    'message': message,
                    'path': field,
                    'sqlcode': e.sqlstate
                }
            })
        )

        res.status_code = 400

        return res


# entrada al formulario de actualición de empleado,
# rellenado previamente con los datos existentes del usuario,
# recuperados según el 'id'
@app.route('/empleados/<id>/edit', methods=['GET'])
@check_auth
def empleado_edit(id=0):
    with UseDatabase(app.config['dbconfig']) as cursor:
        cursor.execute('SELECT * FROM EMPLEADO WHERE id = %s', (id,))
        empleado = dict(
            zip(cursor.column_names, cursor.fetchone()))


    return render_template('empleado.edit.html', data=json.dumps(empleado, use_decimal=True))


# Ruta utilizada para eliminar un empleado según el id,
@app.route('/empleados/<id>', methods=['DELETE'])
@check_auth
def empleado_delete(id=0):
    with UseDatabase(app.config['dbconfig']) as cursor:
        cursor.execute('delete from EMPLEADO where id = %s', (id, ))

    return redirect('/')


if __name__ == '__main__':
    app.run(port=5000, debug=True)
