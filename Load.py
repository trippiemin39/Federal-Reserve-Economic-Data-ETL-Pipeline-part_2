import sqlite3
import csv

def connect_db(datawarehouse):
    conn = sqlite3.connect(datawarehouse)
    return conn


def create_tables(conn):
    cur = conn.cursor()

    cur.execute("""DROP TABLE IF EXISTS dim_indicator;""")
    cur.execute("""DROP TABLE IF EXISTS dim_region;""")
    cur.execute("""DROP TABLE IF EXISTS dim_date;""")
    cur.execute("""DROP TABLE IF EXISTS facttable_observation;""")
    conn.execute("PRAGMA foreign_keys = ON;")

    cur.execute("""CREATE TABLE IF NOT EXISTS dim_indicator(
                    indicator_id INTEGER primary key,
                    indicator_code TEXT,
                    name TEXT,
                    category TEXT,
                    unit TEXT);""")

    cur.execute("""CREATE TABLE IF NOT EXISTS dim_region(
                    region_id INTEGER primary key,
                    region_code TEXT,
                    region_name TEXT);""")

    cur.execute("""CREATE TABLE IF NOT EXISTS dim_date(
                    full_date TEXT,
                    month INTEGER,
                    year INTEGER,
                    quarter INTEGER,
                    month_name TEXT);""")

    cur.execute("""CREATE TABLE IF NOT EXISTS facttable_observation(
                observation_id INTEGER primary key,
                indicator_id INTEGER REFERENCES dim_indicator(indicator_id),
                region_id INTEGER REFERENCES dim_region(region_id),
                date TEXT,
                value FLOAT);""")
    conn.commit()


def load_table(conn, csv_path, table_name, columns):
    cur = conn.cursor()
    with open(csv_path) as f:
        reader = csv.reader(f)
        next(reader)  # skip header

        placeholders = ", ".join(["?"] * len(columns))
        colnames = ", ".join(columns)

        sql = f"INSERT INTO {table_name} ({colnames}) VALUES ({placeholders})"

        cur.executemany(sql, reader)

    conn.commit()


def main():
    conn = connect_db("FREDDY.db")

    create_tables(conn)

    load_table(conn, "DIM_indicator.csv", "dim_indicator",
        ["indicator_id", "indicator_code", "name", "category", "unit"])
    load_table(conn, "DIM_date.csv","dim_date",
        ["full_date", "month", "year", "quarter", "month_name"])
    load_table(conn, "DIM_region.csv", "dim_region",
               ["region_id", "region_code", "region_name"])

    load_table(conn, "facttable.csv", "facttable_observation",
           ["date", "value", "indicator_id", "region_id", "observation_id"])



if __name__ == "__main__":
    main()
