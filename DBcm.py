from mysql.connector import connect


class UseDatabase():

    # constructor, quien acepta la cadena de conexion de la base de datos.
    def __init__(self, config):
        self.config = config

    # apertura de conexion
    def __enter__(self):
        self.conn = connect(**self.config)
        self.cursor = self.conn.cursor()
        return self.cursor

    # cierre de conexion
    def __exit__(self, exc_type, exc_value, trace):
        self.conn.commit()
        self.cursor.close()
        self.conn.close()
