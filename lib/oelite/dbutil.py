import os

def flatten_single_value(rows):
    row = rows.fetchone()
    if row is None:
        return None
    if isinstance(row[0], unicode):
        return str(row[0])
    return row[0]

def flatten_single_column_rows(rows):
    rows = rows.fetchall()
    if not rows:
        return []
    for i in range(len(rows)):
        if isinstance(rows[i][0], unicode):
            rows[i] = str(rows[i][0])
        else:
            rows[i] = rows[i][0]
    return rows

def var_to_tuple(v):
    return (v,)

def tuple_to_var(t):
    return t[0]


def fulldump(db):
    return os.linesep.join([line for line in db.iterdump()])
