import os
import inspect
import oelite.util
import oelite.profiling
import sys
import atexit

query_stats = {}
def write_query_stats():
    if not query_stats:
        return
    with oelite.profiling.profile_output("query_stats.txt") as f:
        for t, l in sorted(query_stats.items()):
            s = oelite.profiling.SimpleStats()
            s.update(l)
            s.compute()
            f.write("%s:%d\t" % (os.path.basename(t[0]), t[1]))
            f.write("%f\t%d\t%f\t" % (s.sum, s.count, s.mean))
            f.write("%s\n" % t[2][0:40])
atexit.register(write_query_stats)

class CursorWrapper(object):
    def __init__(self, cursor, profile=False):
        self.cursor = cursor
        self.profile = profile

    def __getattr__(self, name):
        return getattr(self.cursor, name)

    def execute(self, query, *args, **kwargs):
        if not self.profile:
            return self.cursor.execute(query, *args, **kwargs)

        start = oelite.util.now()
        ret = self.cursor.execute(query, *args, **kwargs)
        stop = oelite.util.now()
        delta = stop-start

        # Some of the code below is stolen from the inspect
        # module. The canonical way would involve using
        # inspect.getframeinfo, but that ends up looking up (and, I
        # think, reading) the entire source file, which is too much
        # overhead for this little excercise. We just want the
        # filename and linenumber.
        #
        # We're duplicating this in executemany rather than putting it
        # in a common helper, since that would require us to inspect
        # another frame (probably number 2).
        frame = sys._getframe(1)
        if inspect.istraceback(frame):
            lineno = frame.tb_lineno
            frame = frame.tb_frame
        else:
            lineno = frame.f_lineno
        filename = inspect.getsourcefile(frame) or inspect.getfile(frame)
        t = (filename, lineno, query)
        try:
            query_stats[t].append(delta)
        except KeyError:
            query_stats[t] = [delta]
        return ret

    def executemany(self, query, *args, **kwargs):
        if not self.profile:
            return self.cursor.executemany(query, *args, **kwargs)

        start = oelite.util.now()
        ret = self.cursor.executemany(query, *args, **kwargs)
        stop = oelite.util.now()
        delta = stop-start

        frame = sys._getframe(1)
        if inspect.istraceback(frame):
            lineno = frame.tb_lineno
            frame = frame.tb_frame
        else:
            lineno = frame.f_lineno
        filename = inspect.getsourcefile(frame) or inspect.getfile(frame)
        t = (filename, lineno, query)
        try:
            query_stats[t].append(delta)
        except KeyError:
            query_stats[t] = [delta]
        return ret

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

def dump_table(dst, db, table):
    c = db.cursor()
    for row in c.execute("SELECT * FROM %s" % table):
        dst.write("\t".join([str(x) for x in row]))
        dst.write("\n")
