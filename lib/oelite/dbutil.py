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
            f.write("%s:%d\t%d" % (os.path.basename(t[0]), t[1], len(l)))

            # Each element in l is a three-element list:
            # 0: #calls of next (or fetch[one,all]) following this query
            # 1: time used in execute/executemany
            # 2: time used in all next/fetchone/fetchall calls
            #
            # Append one element combining 1 and 2, then print 8
            # columns with the sums and averages of all these.
            for x in l:
                x.append(x[1]+x[2])
            for i in range(4):
                s = sum([x[i] for x in l])
                if i == 0:
                    f.write("\t%d\t%f" % (s, float(s)/len(l)))
                else:
                    f.write("\t%f\t%f" % (s, s/len(l)))

            f.write("\t%s\n" % t[2][0:40])
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
        self.current_record = record = [0, delta, 0]
        try:
            query_stats[t].append(record)
        except KeyError:
            query_stats[t] = [record]

        # SELECT statements return the cursor object itself, but we
        # need to also be able to intercept all the .next calls to
        # really measure how expensive this query ends up being. Other
        # queries may return None, and we don't want to interfere with
        # that.
        if ret is self.cursor:
            return self
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
        self.current_record = record = [0, delta, 0]
        try:
            query_stats[t].append(record)
        except KeyError:
            query_stats[t] = [record]

        if ret is self.cursor:
            return self
        return ret

    def __iter__(self):
        return self

    # This is Python 2, so we have to define .next rather than .__next__ .
    def next(self):
        if not self.profile:
            # This should never really happen.
            return self.cursor.next()

        start = oelite.util.now()
        try:
            return self.cursor.next()
        finally:
            stop = oelite.util.now()
            delta = stop-start
            self.current_record[0] += 1
            self.current_record[2] += delta

    def fetchone(self):
        if not self.profile:
            # This should never really happen.
            return self.cursor.fetchone()

        start = oelite.util.now()
        try:
            return self.cursor.fetchone()
        finally:
            stop = oelite.util.now()
            delta = stop-start
            self.current_record[0] += 1
            self.current_record[2] += delta

    def fetchall(self):
        if not self.profile:
            # This should never really happen.
            return self.cursor.fetchall()

        start = oelite.util.now()
        try:
            return self.cursor.fetchall()
        finally:
            stop = oelite.util.now()
            delta = stop-start
            self.current_record[0] += 1
            self.current_record[2] += delta

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
