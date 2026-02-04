import sqlite3

def execute_sql(schema: str, sql: str):
    conn = sqlite3.connect(":memory:")
    cur = conn.cursor()

    try:
        for stmt in schema.split(";"):
            if stmt.strip():
                cur.execute(stmt)

        cur.execute(sql)
        rows = cur.fetchall()

        return {
            "row_count": len(rows),
            "columns": [d[0] for d in cur.description]
        }
    finally:
        conn.close()