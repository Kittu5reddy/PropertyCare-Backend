import psycopg2
import os
import dotenv

dotenv.load_dotenv()
dotenv.load_dotenv('.env.prod')

def check_db_connection():
    conn=0
    user=0
    try:
        conn = psycopg2.connect(
    dbname=os.getenv('DATABASE_NAME'),
    user=os.getenv('USERNAME'),
    password=os.getenv('PASSWORD'),
    host=os.getenv('HOST_NAME'),
    port=os.getenv('PORT_ID')  # ✅ NOT quoted
)
        print(os.getenv('USERNAME'))
        print("✅ Connection successful")
    except Exception as e:
        print("❌ Connection failed:", e)
        return
    return conn


def check_table_exists(conn, table_name):
    cursor = conn.cursor()
    cursor.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_schema = 'public' AND table_name = %s
        );
    """, (table_name,))
    exists = cursor.fetchone()[0]
    cursor.close()
    print( f"✅ {table_name} successful" if exists else f"❌ {table_name} failed ")





































if __name__=="__main__":
    conn=check_db_connection()
    check_table_exists(conn,'users')
    check_table_exists(conn,'personal_details')
    check_table_exists(conn,'documents')
