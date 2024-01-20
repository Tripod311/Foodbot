import sqlite3

# conn = sqlite3.connect("./foods.sql")
# conn.execute("CREATE TABLE IF NOT EXISTS foods (vitamin VARCHAR(300), product VARCHAR(300));")
#
#
# def add_vitamin(vit_name, product_list):
#     sp = product_list.split(',')
#     normalized = []
#     for p in sp:
#         normalized.append(p.strip().lower())
#     script = []
#     for p in normalized:
#         script.append("INSERT INTO foods (vitamin, product) VALUES (\"" + vit_name + "\",\"" + p + "\")")
#     conn.executescript(";".join(script))


def find_minimal():
    conn = sqlite3.connect("./foods.sql")
    cur = conn.execute("SELECT DISTINCT vitamin FROM foods")
    res = cur.fetchall()
    vitamins = []
    for row in res:
        vitamins.append(row[0])
    cur.close()
    vit_closed = {}
    for vit in vitamins:
        vit_closed[vit] = False
    cur = conn.execute("SELECT DISTINCT product FROM foods")
    res = cur.fetchall()
    products = {}
    for row in res:
        products[row[0]] = 0
    cur.close()
    for k in products:
        cur = conn.execute("SELECT COUNT(*) FROM foods WHERE product=?", [k])
        products[k] = cur.fetchone()[0]
        cur.close()
    sorted_products = []
    for k in products:
        index = 0
        count = products[k]
        while index < len(sorted_products) and sorted_products[index][1] > count:
            index = index + 1
        sorted_products.insert(index, (k, count))
    has_dangling = True
    product_index = 0
    minimal_arr = []
    while has_dangling:
        product = sorted_products[product_index][0]
        affects = 0
        cur = conn.execute("SELECT vitamin FROM foods WHERE product=?", [product])
        vit_list = cur.fetchall()
        cur.close()
        for row in vit_list:
            vit = row[0]
            if not vit_closed[vit]:
                affects = affects + 1
                vit_closed[vit] = True
        if affects > 0:
            minimal_arr.append(product)
        product_index = product_index + 1
        has_dangling = False
        for k in vit_closed:
            if not vit_closed[k]:
                has_dangling = True
    conn.close()
    return minimal_arr


# def find_efficient(exclude_set, limit=3):
#     cur = conn.execute("SELECT DISTINCT vitamin FROM foods")
#     res = cur.fetchall()
#     vitamins = []
#     for row in res:
#         vitamins.append(row[0])
#     cur.close()
#     leading_products = []
#     for vit in vitamins:
#         cur = conn.execute("SELECT product FROM foods WHERE vitamin=? LIMIT ?", [vit, limit])
#         leaders = cur.fetchall()
#         for row in leaders:
#             product = row[0]
#             if product in exclude_set:
#                 continue
#             leading_products.append(row[0])
#     result = set(leading_products)
#     return list(result)


def check_completeness(product_set):
    conn = sqlite3.connect("./foods.sql")
    cur = conn.execute("SELECT DISTINCT vitamin FROM foods")
    res = cur.fetchall()
    vitamins = []
    for row in res:
        vitamins.append(row[0])
    cur.close()
    mod = []
    for name in product_set:
        mod.append('"' + name + '"')
    set_line = ", ".join(mod)
    set_line = "(" + set_line + ")"
    query = "SELECT COUNT(*) FROM foods WHERE product IN " + set_line + " AND vitamin=?;"
    unfilled = []
    for vit in vitamins:
        cur = conn.execute(query, [vit])
        res = cur.fetchone()[0]
        if res == 0:
            unfilled.append(vit)
        cur.close()
    conn.close()
    return unfilled


def only_first(exclude_set, per_count=1):
    conn = sqlite3.connect("./foods.sql")
    cur = conn.execute("SELECT DISTINCT vitamin FROM foods")
    res = cur.fetchall()
    vitamins = []
    for row in res:
        vitamins.append(row[0])
    cur.close()
    leading_products = []
    for vit in vitamins:
        cur = conn.execute("SELECT product FROM foods WHERE vitamin=?", [vit])
        leaders = cur.fetchall()
        counter = 0
        for row in leaders:
            product = row[0]
            if product in exclude_set:
                continue
            leading_products.append(product)
            counter = counter + 1
            if per_count > 0 and counter == per_count:
                break
    result = set(leading_products)
    conn.close()
    result = list(result)
    result.sort()
    return result


def get_nutrient_list():
    conn = sqlite3.connect("./foods.sql")
    cur = conn.execute("SELECT DISTINCT vitamin FROM foods")
    rows = cur.fetchall()
    cur.close()
    result = []
    for row in rows:
        result.append(row[0])
    conn.close()
    return result


def get_product_list():
    conn = sqlite3.connect("./foods.sql")
    cur = conn.execute("SELECT DISTINCT product FROM foods")
    rows = cur.fetchall()
    cur.close()
    result = []
    for row in rows:
        result.append(row[0])
    conn.close()
    return result


def get_product_for_nutrient(nutrient):
    conn = sqlite3.connect("./foods.sql")
    cur = conn.execute("SELECT product FROM foods WHERE vitamin like ?", [nutrient])
    rows = cur.fetchall()
    cur.close()
    result = []
    for row in rows:
        result.append(row[0])
    conn.close()
    return result


def get_nutrient_in_product(product):
    conn = sqlite3.connect("./foods.sql")
    cur = conn.execute("SELECT vitamin FROM foods WHERE product like ?", [product])
    rows = cur.fetchall()
    cur.close()
    result = []
    for row in rows:
        result.append(row[0])
    conn.close()
    return result
