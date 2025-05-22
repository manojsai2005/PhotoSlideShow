# import mysql.connector
# from datetime import datetime

# db_config = {
#     'host': 'localhost',
#     'user': 'Varun',
#     'password': 'Varun@123',
#     'database': 'users'
# }

# file_name = '[iSongs.info] 01 - Gusa Gusa Lade.mp3'
# file_path = '/home/home/Downloads/[iSongs.info] 01 - Gusa Gusa Lade.mp3'


# connection = mysql.connector.connect(**db_config)
# cursor = connection.cursor()

# try:
#     with open(file_path, 'rb') as file:
#         blob_data = file.read()

#     insert_query = """
#     INSERT INTO AudioFiles (file_name, BlobData)
#     VALUES (%s, %s)
#     """

#     data = (file_name, blob_data)

#     cursor.execute(insert_query, data)
#     connection.commit()
#     print("Audio file with BlobData inserted successfully.")
# except Exception as e:
#     print(f"Error: {e}")
#     connection.rollback()
# finally:
#     cursor.close()
#     connection.close()

import mysql.connector
from datetime import datetime
from psycopg2.extras import DictCursor
from urllib.parse import urlparse
import psycopg2
url = urlparse("postgresql://varun:Gte0P03BF2I_Fs9XUj5f-g@field-troll-9043.8nk.gcp-asia-southeast1.cockroachlabs.cloud:26257/group_35?sslmode=verify-full")

db_params = {
    'dbname': url.path[1:],
    'user': url.username,
    'password': url.password,
    'host': url.hostname,
    'port': url.port
}
connections = psycopg2.connect(**db_params)
cursor = connections.cursor()
musicid = 7
file_name = 'vellake.mp3'
file_path = '/home/home/Downloads/vellakemp3'




try:
    with open(file_path, 'rb') as file:
        blobdata = file.read()

    insert_query = """
    INSERT INTO AudioFiles (musicid,file_name, blob_data)
    VALUES (%s, %s, %s)
    """

    data = (musicid,file_name, blobdata)

    cursor.execute(insert_query, data)
    connections.commit()
    print("Audio file with BlobData inserted successfully.")
except Exception as e:
    print(f"Error: {e}")
    connections.rollback()
finally:
    cursor.close()
    connections.close()