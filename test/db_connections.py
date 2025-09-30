import psycopg2

try:
    conn = psycopg2.connect(
        dbname="propcare",
        user="kittu",
        password="kaushik",
        host="31.97.228.13",
        port="5432"
    )
    print("✅ Connected successfdcscsully")

    cur = conn.cursor()

    # Optional: Ensure schema exists
    cur.execute("CREATE SCHEMA IF NOT EXISTS PropCare;")

    # Create table within the schema
    create_table_query = """
    CREATE TABLE IF NOT EXISTS PropCare.demo (
        id SERIAL PRIMARY KEY,
        name VARCHAR(100),
        department VARCHAR(50),
        salary NUMERIC
    );
    """
    cur.execute(create_table_query)
    conn.commit()
    print("✅ Table 'employees' created successfully in schema 'PropCare'")

    cur.close()
    conn.close()

except Exception as e:
    print("❌ Connection or table creation failed:", e)
