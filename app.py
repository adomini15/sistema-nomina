from flask import Flask, render_template, request, redirect, make_response, jsonify
from DBcm import UseDatabase
from mysql.connector import Error
import simplejson as json
from auth import check_auth
from datetime import datetime, timedelta
import jwt
import re
import bcrypt

app = Flask(__name__)

app.config['dbconfig'] = {
    'host': 'localhost',
    'username': 'odil',
    'passwd': '123456',
    'db': 'SISTEMA_NOMINA'
}

app.config['SECRET_KEY'] = 'YouNeverBeAbleToDestroyMe'

custom_errors = {
    '23000': 'Dato existente.'
}


@app.route('/auth', methods=['POST'])
def authentication():
    try:
        with UseDatabase(app.config['dbconfig']) as cursor:
            _SQL = "SELECT id, contrasena FROM USUARIO WHERE nombre=%s"

            cursor.execute(_SQL, (request.form['nombre'],))

            hashed_passwd = cursor.fetchone()

            if not hashed_passwd:
                res = make_response(jsonify({
                    'error': {'message': 'Nombre incorrecto.', 'path': 'nombre'}
                }))

                res.status_code = 400

                return res

            id = hashed_passwd[0]
            hashed_passwd = hashed_passwd[1].encode('utf8')

            if not bcrypt.checkpw(request.form['contrasena'].encode('utf8'), hashed_passwd):  # noqa: E501
                res = make_response(jsonify({
                    'error': {'message': 'Contrasena incorrecta.', 'path': 'contrasena'}  # noqa: E501
                }))

                res.status_code = 400

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


@app.route('/signin')
def signin():
    return render_template('login.html')


@app.route('/signup')
def usuario_create():
    return render_template('usuario.create.html')


@app.route('/usuarios', methods=['POST'])
def usuario_add():
    try:
        with UseDatabase(app.config['dbconfig']) as cursor:
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


@app.route('/', methods=['GET'])
@app.route('/empleados', methods=['GET'])
@check_auth
def index():

    with UseDatabase(app.config['dbconfig']) as cursor:
        cursor.execute('select * from EMPLEADO')
        empleados = cursor.fetchall()

    return render_template(
        'index.html', empleados=empleados, columns=cursor.column_names
        )


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


@app.route('/empleados/create')
@check_auth
def empleado_create():
    return render_template('empleado.create.html')


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


@app.route('/empleados/<id>/edit', methods=['GET'])
@check_auth
def empleado_edit(id=0):
    with UseDatabase(app.config['dbconfig']) as cursor:
        cursor.execute('SELECT * FROM EMPLEADO WHERE id = %s', (id,))
        empleado = dict(
            zip(cursor.column_names, cursor.fetchone()))


    return render_template('empleado.edit.html', data=json.dumps(empleado, use_decimal=True))


@app.route('/empleados/<id>', methods=['DELETE'])
@check_auth
def empleado_delete(id=0):
    with UseDatabase(app.config['dbconfig']) as cursor:
        cursor.execute('delete from EMPLEADO where id = %s', (id, ))

    return redirect('/')


if __name__ == '__main__':
    app.run(port=5000, debug=True)
