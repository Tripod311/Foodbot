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
    conn = sqlite3.connect("foods_new.sql")
    # get nutrients list
    cur = conn.execute("""SELECT name,alias FROM nutrients""")
    raw = cur.fetchall()
    nutrients = {}
    for row in raw:
        nutrients[row[0]] = {
            "alias": row[1],
            "warning": False,
            "fatal": False,
            "products": []
        }
    cur.close()
    # get products list for each nutrient
    for n in nutrients:
        nutrient_obj = nutrients[n]
        alias = nutrient_obj["alias"]
        cur = conn.execute(f"""SELECT products.name FROM {alias}
        LEFT JOIN products ON {alias}.product_id=products.rowid
        ORDER BY {alias}.amount DESC""")
        raw = cur.fetchall()
        counter = 0
        index = 0
        while index < len(raw) and counter < products_per_nutrient:
            product_name = raw[index][0]
            index = index + 1
            if product_name not in exclude_set:
                counter = counter + 1
                nutrient_obj["products"].append(product_name)
        if counter == 0:
            nutrient_obj["fatal"] = True
        elif index > 6:
            nutrient_obj["warning"] = True
    result_list = []
    warn_list = []
    fatal_list = []
    for n in nutrients:
        result_list = result_list + nutrients[n]["products"]
        if nutrients[n]["warning"]:
            warn_list.append(n)
        if nutrients[n]["fatal"]:
            fatal_list.append(n)
    result_list = set(result_list)
    result_list = list(result_list)
    result_list.sort()
    conn.close()
    return (result_list, warn_list, fatal_list)


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
    cur = conn.execute("SELECT alias, daily FROM nutrients WHERE name=?", [n_name])
    raw = cur.fetchone()
    if raw is None:
        cur.close()
        conn.close()
        return None
    else:
        alias = raw[0]
        daily = raw[1]
        cur.close()
        cur = conn.execute(f"""SELECT products.name, {alias}.amount FROM {alias}
        LEFT JOIN products ON {alias}.product_id = products.rowid
        ORDER BY {alias}.amount DESC""")
        raw = cur.fetchall()
        arr = []
        for row in raw:
            arr.append(row[0] + " - {:.2f}%".format(row[1]/daily * 100))
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


def get_product_ratings(product_set):
    result = []
    conn = sqlite3.connect("foods_new.sql")
    for product in product_set:
        rating = 0
        cur = conn.execute("""SELECT products.rowid, nutrients.alias, nutrients.daily FROM relations
        LEFT JOIN products ON relations.product_id=products.rowid
        LEFT JOIN nutrients ON relations.nutrient_id=nutrients.rowid
        WHERE products.name=?""", [product])
        for row in cur.fetchall():
            product_id = row[0]
            alias = row[1]
            daily = row[2]
            p_c = conn.execute(f"SELECT amount FROM {alias} WHERE product_id=?", [product_id])
            product_amount = p_c.fetchone()[0]
            rating = rating + min(1, product_amount/daily)
            p_c.close()
        cur.close()
        index = 0
        while index < len(result) and result[index][1] > rating:
            index = index + 1
        result.insert(index, (product, rating))
    conn.close()
    return result


def get_csv():
    nutrient_list = get_nutrient_list()
    n_products = []
    max_product_length = 0
    for n in nutrient_list:
        n_p = get_products_for_nutrient(n)
        max_product_length = max(max_product_length, len(n_p))
        n_products.append(n_p)
    csv = [
        ";".join(nutrient_list)
    ]
    for i in range(0, max_product_length):
        line = []
        for prod_list in n_products:
            if i < len(prod_list):
                line.append(prod_list[i])
            else:
                line.append("")
        csv.append(";".join(line))
    return "\n".join(csv)
