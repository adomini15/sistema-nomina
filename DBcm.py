from mysql.connector import connect


class UseDatabase():
    def __init__(self, config):
        self.config = config

    def __enter__(self):
        self.conn = connect(**self.config)
        self.cursor = self.conn.cursor()
        return self.cursor

    def __exit__(self, exc_type, exc_value, trace):
        self.conn.commit()
        self.cursor.close()
        self.conn.close()
