import pymysql

def get_connection():
    print("🔗 DB 연결 중...")
    return pymysql.connect(
        host='localhost',
        port=3306,
        user='{username}',
        password='{password}}',
        database='{database}',
        charset='utf8mb4',
        autocommit=False,
        cursorclass=pymysql.cursors.DictCursor
    )
