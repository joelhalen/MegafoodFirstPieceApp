import sqlite3

import mysql.connector
import configparser

class DatabaseManager:
    def __init__(self):
        ## load stored config from file
        config = configparser.ConfigParser()
        config.read('config.cfg')
        ## Decide whether to locally or externally store data
        self.use_sqlite = config.getboolean('DatabaseSettings', 'use_sqlite')
        self.use_external_db = config.getboolean('DatabaseSettings', 'use_external_db')
        ## Load external database connection, if configured
        if self.use_external_db:
            self.external_db_config = {
                'host': config.get('ExternalDB', 'host'),
                'database': config.get('ExternalDB', 'database'),
                'user': config.get('ExternalDB', 'user'),
                'password': config.get('ExternalDB', 'password')
            }
        else:
            # Otherwise resort to SQLite storage (local-only)
            self.external_db_config = None

        self.db_path = "qc_application.db"
        self.initialize_database()

    def initialize_database(self):
        if self.use_sqlite:
            self.conn = sqlite3.connect(self.db_path)
            self.cursor = self.conn.cursor()
        elif self.use_external_db and self.external_db_config:
            self.conn = mysql.connector.connect(**self.external_db_config)
            self.cursor = self.conn.cursor()
        else:
            # Initialize file-based storage system
            pass
        self.create_tables()

    def create_tables(self):
        users_table = '''CREATE TABLE IF NOT EXISTS users
                         (username VARCHAR(255) PRIMARY KEY, pin TEXT) ENGINE=InnoDB;'''
        blends_table = '''CREATE TABLE IF NOT EXISTS blends
                          (code VARCHAR(255) PRIMARY KEY, product TEXT, tablets_amount INTEGER, kilos_to_produce REAL, tablet_size VARCHAR(255), tablet_weight REAL) ENGINE=InnoDB;'''
        lot_images_table = '''CREATE TABLE IF NOT EXISTS lot_images
                              (blend_code VARCHAR(255), lot_number VARCHAR(255), image_path TEXT, FOREIGN KEY(blend_code) REFERENCES blends(code),
                              confirmed_by VARCHAR(255)) ENGINE=InnoDB;'''
        if self.use_sqlite or self.use_external_db:
            self.cursor.execute(users_table)
            self.cursor.execute(blends_table)
            self.cursor.execute(lot_images_table)
            self.conn.commit()
        else:
            # Create tables in file-based storage, if applicable
            pass

    def fetch_all_users(self):
        self.cursor.execute("SELECT username FROM users")
        columns = [col[0] for col in self.cursor.description]
        return [dict(zip(columns, row)) for row in self.cursor.fetchall()]

    def authenticate_user(self, username, pin):
        self.cursor.execute("SELECT * FROM users WHERE username = %s AND pin = %s", (username, pin))
        return self.cursor.fetchone() is not None

    def close(self):
        if self.use_sqlite or self.use_external_db:
            self.conn.close()

    def insert_blend(self, code, product, tablets_amount, kilos_to_produce, tablet_size, tablet_weight):
        if self.use_sqlite:
            query = '''INSERT INTO blends (code, product, tablets_amount, kilos_to_produce, tablet_size, tablet_weight)
                       VALUES (?, ?, ?, ?, ?, ?)'''
        else:
            query = '''INSERT INTO blends (code, product, tablets_amount, kilos_to_produce, tablet_size, tablet_weight)
                               VALUES (%s, %s, %s, %s, %s, %s)'''
        try:
            self.cursor.execute(query, (code, product, tablets_amount, kilos_to_produce, tablet_size, tablet_weight))
            self.conn.commit()
        except Exception as e:
            print(f"An error occurred: {e}")
            self.conn.rollback()

    def fetch_blend_info(self, blend_code):
        query = '''SELECT * FROM blends WHERE code = %s'''

        try:
            self.cursor.execute(query, (blend_code,))
            result = self.cursor.fetchone()

            if result:
                blend_info = {
                    'code': result[0],
                    'product': result[1],
                    'tablets_amount': result[2],
                    'kilos_to_produce': result[3],
                    'tablet_size': result[4],
                    'tablet_weight': result[5]
                }
                return blend_info
            else:
                return None  # Blend with the specified code not found

        except Exception as e:
            print(f"An error occurred while fetching blend info: {e}")
            return None

    def fetch_valid_blends(self):
        query = "SELECT code FROM blends WHERE tablet_weight IS NOT NULL AND tablet_weight > 0"
        self.cursor.execute(query)
        return [row[0] for row in self.cursor.fetchall()]

    def create_image_table(self):
        image_table = '''CREATE TABLE IF NOT EXISTS lot_images (
            id INT AUTO_INCREMENT PRIMARY KEY,
            blend_code VARCHAR(255),
            lot_number INT,
            result TEXT,
            image_path TEXT,
            FOREIGN KEY(blend_code) REFERENCES blends(code)
        ) ENGINE=InnoDB;'''
        self.cursor.execute(image_table)
        self.conn.commit()

    def find_next_lot(self, blend_id):
        if self.use_sqlite:
            query = "SELECT MAX(lot_number) FROM lot_images WHERE blend_code = ?"
        else:
            query = "SELECT MAX(lot_number) FROM lot_images WHERE blend_code = %s"
        self.cursor.execute(query, (blend_id,))
        result = self.cursor.fetchone()
        if result and result[0] is not None:
            # Convert the lot number to an integer before adding 1
            return int(result[0]) + 1
        else:
            return 0  # Start with 1 if no lots are found

    def fetch_image_info_for_blend(self, blend_id):
        if self.use_sqlite:
            query = "SELECT image_path, lot_number FROM lot_images WHERE blend_code = ? ORDER BY lot_number DESC LIMIT 1"
        else:  # Assuming MySQL/MariaDB for external DB
            query = "SELECT image_path, lot_number FROM lot_images WHERE blend_code = %s ORDER BY lot_number DESC LIMIT 1"

        self.cursor.execute(query, (blend_id,))
        result = self.cursor.fetchone()
        if result:
            return result[0], result[1]  # image_path, lot_number
        else:
            return None, None

    def fetch_lot_numbers_for_blend(self, blend_id):
        if not self.use_sqlite:
            query = "SELECT lot_number FROM lot_images WHERE blend_code = %s ORDER BY lot_number DESC"
        else:
            query = "SELECT lot_number FROM lot_images WHERE blend_code = ? ORDER BY lot_number DESC"
        self.cursor.execute(query, (blend_id,))
        # Fetch all matching records and extract the lot number of each
        lot_numbers = [row[0] for row in self.cursor.fetchall()]
        return lot_numbers

    def insert_lot_image(self, blend_code, lot_number, image_path):
        if self.use_sqlite:
            query = '''INSERT INTO lot_images (blend_code, lot_number, image_path, confirmed_by)
                       VALUES (?, ?, ?, ?)'''
            params = (blend_code, lot_number, image_path, "")
        else:  # For MySQL/MariaDB
            query = '''INSERT INTO lot_images (blend_code, lot_number, image_path, confirmed_by)
                       VALUES (%s, %s, %s, %s)'''
            params = (blend_code, lot_number, image_path, "")

        try:
            self.cursor.execute(query, params)
            self.conn.commit()
        except Exception as e:
            print(f"An error occurred while inserting lot image: {e}")
            self.conn.rollback()

    def mark_confirmed(self, user_initials, blend_code, lot_number):
        print(f"Marking lot {lot_number} as confirmed by {user_initials}")
        query = '''UPDATE lot_images SET confirmed_by = %s 
        WHERE blend_code = %s AND lot_number = %s'''
        params = (user_initials, blend_code, lot_number)
        try:
            self.cursor.execute(query, params)
            self.conn.commit()
        except Exception as e:
            print(f"Couldn't mark the lot as confirmed... {e}")
            self.conn.rollback()


