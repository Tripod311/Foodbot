import sqlite3


def find_minimal():
    conn = sqlite3.connect("foods_new.sql")
    # get product list with frequency
    cur = conn.execute("""SELECT products.rowid, products.name FROM relations
    LEFT JOIN products ON relations.product_id = products.rowid
    GROUP BY relations.product_id ORDER BY COUNT(*) DESC""")
    raw = cur.fetchall()
    products = []
    for row in raw:
        products.append((row[0], row[1]))
    cur.close()
    # get nutrients list
    cur = conn.execute("""SELECT name FROM nutrients""")
    raw = cur.fetchall()
    nutrients = {}
    for row in raw:
        nutrients[row[0]] = False
    cur.close()
    # go top-down and cross out nutrients
    has_dangling = True
    product_index = 0
    result = []
    while has_dangling:
        product = products[product_index]
        product_id = product[0]
        product_name = product[1]
        cur = conn.execute("""SELECT nutrients.name FROM relations
        LEFT JOIN nutrients ON relations.nutrient_id=nutrients.rowid
        WHERE relations.product_id = ?""", [product_id])
        raw = cur.fetchall()
        include = False
        for row in raw:
            n_name = row[0]
            if not nutrients[n_name]:
                include = True
                nutrients[n_name] = True
        cur.close()
        if include:
            result.append(product_name)
        product_index = product_index + 1
        has_dangling = False
        for n in nutrients:
            if not nutrients[n]:
                has_dangling = True
                break
    conn.close()
    return result


def check_completeness(product_set):
    set_string = ['"' + x + '"' for x in product_set]
    set_string = "(" + ",".join(set_string) + ")"
    conn = sqlite3.connect("foods_new.sql")
    cur = conn.execute(f"""SELECT nutrients.name FROM nutrients
    EXCEPT
    SELECT nutrients.name FROM relations
    LEFT JOIN nutrients ON relations.nutrient_id=nutrients.rowid
    LEFT JOIN products ON relations.product_id=products.rowid
    WHERE products.name IN {set_string}""")
    unfilled = []
    nut = cur.fetchone()
    while nut is not None:
        unfilled.append(nut[0])
        nut = cur.fetchone()
    conn.close()
    return unfilled


def generate_list(exclude_set, products_per_nutrient=1):
    pass


def get_nutrient_list():
    conn = sqlite3.connect("foods_new.sql")
    cur = conn.execute("SELECT name FROM nutrients ORDER BY name ASC")
    arr = []
    raw = cur.fetchall()
    for row in raw:
        arr.append(row[0])
    cur.close()
    conn.close()
    return arr


def get_product_list():
    conn = sqlite3.connect("foods_new.sql")
    cur = conn.execute("SELECT name FROM products ORDER BY name ASC")
    arr = []
    raw = cur.fetchall()
    for row in raw:
        arr.append(row[0])
    cur.close()
    conn.close()
    return arr


def get_products_for_nutrient(n_name):
    conn = sqlite3.connect("foods_new.sql")
    cur = conn.execute("SELECT alias FROM nutrients WHERE name=?", [n_name])
    raw = cur.fetchone()
    if raw is None:
        cur.close()
        conn.close()
        return None
    else:
        alias = raw[0]
        cur.close()
        cur = conn.execute(f"""SELECT products.name FROM {alias}
        LEFT JOIN products ON {alias}.product_id = products.rowid
        ORDER BY {alias}.amount DESC""")
        raw = cur.fetchall()
        arr = []
        for row in raw:
            arr.append(row[0])
        cur.close()
        conn.close()
        return arr


def get_nutrients_in_product(p_name):
    conn = sqlite3.connect("foods_new.sql")
    cur = conn.execute("SELECT rowid FROM products WHERE name=?", [p_name])
    raw = cur.fetchone()
    if raw is None:
        cur.close()
        conn.close()
        return None
    else:
        product_id = raw[0]
        cur.close()
        cur = conn.execute(f"""SELECT nutrients.name FROM relations
        LEFT JOIN nutrients ON relations.nutrient_id = nutrients.rowid
        WHERE relations.product_id=?""", [product_id])
        raw = cur.fetchall()
        arr = []
        for row in raw:
            arr.append(row[0])
        cur.close()
        conn.close()
        return arr
