import sqlite3
import json

conn = sqlite3.connect("foods_new.sql")
# cur = conn.execute(f"""CREATE TABLE IF NOT EXISTS products (
# name VARCHAR(300) UNIQUE
# )""")
# cur.close()
# cur = conn.execute(f"""CREATE TABLE IF NOT EXISTS nutrients (
# name VARCHAR(300) UNIQUE,
# alias VARCHAR(300)
# )""")
# cur.close()
# cur = conn.execute(f"""CREATE TABLE IF NOT EXISTS relations (
# product_id INTEGER,
# nutrient_id INTEGER
# )""")
# cur.close()


def add_nutrient(alias, nutrient_name, products):
    cur = conn.execute(f"""CREATE TABLE IF NOT EXISTS {alias} (
product_id INTEGER,
amount REAL);""")
    cur.close()
    cur = conn.execute("INSERT INTO nutrients (name, alias) VALUES (?, ?)", [nutrient_name, alias])
    cur.close()
    cur = conn.execute("SELECT rowid FROM nutrients WHERE name=?", [nutrient_name])
    nutrient_id = cur.fetchone()[0]
    cur.close()
    product_map = {}
    for pair in products:
        product_name = pair[0]
        amount = pair[1]
        if product_name in product_map:
            if product_map[product_name] > amount:
                product_map[product_name] = amount
        else:
            product_map[product_name] = amount

    for product_name in product_map:
        amount = product_map[product_name]
        product_id = -1
        # search product name
        cur = conn.execute("SELECT rowid FROM products WHERE name=?", [product_name])
        row = cur.fetchone()
        if row is None:
            cur = conn.execute("INSERT INTO products (name) VALUES (?)", [product_name])
            cur.close()
            cur = conn.execute("SELECT rowid FROM products WHERE name=?", [product_name])
            product_id = cur.fetchone()[0]
        else:
            product_id = row[0]
        cur = conn.execute("INSERT INTO relations (product_id, nutrient_id) VALUES (?, ?)", [product_id, nutrient_id])
        cur.close()
        cur = conn.execute(f"INSERT INTO {alias} (product_id, amount) VALUES (?, ?)", [product_id, amount])
        cur.close()


# f = open("./base.json")
# data = json.load(f)
# f.close()

# count products
# l = []
# for nutrient in data:
#     for product in nutrient["products"]:
#         l.append(product[0])
# l = set(l)
# l = list(l)
# l.sort()
# print("Продуктов " + str(len(l)))
# print("\n".join(l))

# for nutrient in data:
#     alias = nutrient["alias"]
#     name = nutrient["name"]
#     products = nutrient["products"]
#     add_nutrient(alias, name, products)
#
# conn.commit()


compare_list = [
    "овес",
    "кукуруза",
    "киноа",
    "гречка",
    "булгур",
    "рис",
    "кускус"
]
ratings = {}

for product_name in compare_list:
    # get product id
    cur = conn.execute("SELECT rowid FROM products WHERE name=?", [product_name])
    product_id = cur.fetchone()[0]
    cur.close()
    # count elements
    cur = conn.execute("SELECT nutrient_id FROM relations WHERE product_id=?", [product_id])
    nutrients = []
    raw = cur.fetchall()
    for row in raw:
        nutrients.append(row[0])
    cur.close()
    # calculate rating for each nutrient
    result = 0
    for n_id in nutrients:
        # 0.5 for each nutrient
        result = result + 0.5
        # get nutrient alias
        cur = conn.execute("SELECT alias FROM nutrients WHERE rowid=?", [n_id])
        alias = cur.fetchone()[0]
        cur.close()
        # calculate
        product_row = -1
        cur = conn.execute(f"SELECT product_id,amount FROM {alias} ORDER BY AMOUNT DESC")
        raw_rows = cur.fetchall()
        rows = []
        for row in raw_rows:
            if row[0] == product_id:
                product_row = row[0]
            rows.append((row[0], row[1]))
        cur.close()
        result = result + product_row/len(rows)
    ratings[product_name] = result

print(ratings)

conn.close()
