import os

def flatten_single_value(rows):
    row = rows.fetchone()
    if row is None:
        return None
    return row[0]

def flatten_single_column_rows(rows):
    rows = rows.fetchall()
    if not rows:
        return []
    for i in range(len(rows)):
        rows[i] = rows[i][0]
    return rows

def var_to_tuple(v):
    return (v,)

def tuple_to_var(t):
    return t[0]


def fulldump(db):
    return os.linesep.join([line for line in db.iterdump()])
