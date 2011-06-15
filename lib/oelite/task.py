from oebakery import die, err, warn, info, debug
import oelite.meta
import oelite.recipe
from oelite.dbutil import *

import sys
import os

def task_name(name):
    if name.startswith("do_"):
        return name
    return "do_" + name


class OEliteTask:

    def __init__(self, id, recipe, name, nostamp, cookbook):
        self.id = id
        self.recipe = cookbook.get_recipe(id=recipe)
        self.name = name
        self.nostamp = nostamp
        self.cookbook = cookbook
        return

    def __str__(self):
        return "%s:%s"%(self.recipe, self.name)


    def get_parents(self):
        task_ids = flatten_single_column_rows(self.cookbook.dbc.execute(
            "SELECT parent FROM task_parent WHERE task=?",
            (self.id,)))
        return self.cookbook.get_tasks(id=task_ids)

    def get_deptasks(self):
        return flatten_single_column_rows(self.cookbook.dbc.execute(
            "SELECT deptask FROM task_deptask WHERE task=?",
            (self.id,)))

    def get_rdeptasks(self):
        return flatten_single_column_rows(self.cookbook.dbc.execute(
            "SELECT rdeptask FROM task_rdeptask WHERE task=?",
            (self.id,)))

    def get_recdeptasks(self):
        return flatten_single_column_rows(self.cookbook.dbc.execute(
            "SELECT recdeptask FROM task_recdeptask WHERE task=?",
            (self.id,)))

    def get_recrdeptasks(self):
        return flatten_single_column_rows(self.cookbook.dbc.execute(
            "SELECT recrdeptask FROM task_recrdeptask WHERE task=?",
            (self.id,)))

    def get_recadeptasks(self):
        return flatten_single_column_rows(self.cookbook.dbc.execute(
            "SELECT recadeptask FROM task_recadeptask WHERE task=?",
            (self.id,)))

    def get_taskdepends(self):
        return flatten_single_column_rows(self.cookbook.dbc.execute(
            "SELECT parent_item, parent_task FROM task_depend WHERE task=?",
            (self.id,)))


    def stampfile_path(self):
        try:
            return self._stampfile
        except AttributeError:
            stampdir = self.recipe.get("STAMPDIR")
            self._stampfile = (stampdir, os.path.join(stampdir, self.name))
        return self._stampfile


    # return (mtime, hash) from stamp file
    def read_stamp(self):
        stampfile = self.stampfile_path()[1]
        if not os.path.exists(stampfile):
            return (None, None)
        if not os.path.isfile(stampfile):
            die("bad hash file: %s"%(stampfile))
        if os.path.getsize(stampfile) == 0:
            return (None, None)
        mtime = os.stat(stampfile).st_mtime
        with open(stampfile, "r") as stampfile:
            tmphash = stampfile.read()
        return (mtime, tmphash)


    def build_started(self):
        if self.nostamp:
            return
        (stampdir, stampfile) = self.stampfile_path()
        if not os.path.exists(stampdir):
            os.makedirs(stampdir)
        open(stampfile, "w").close()
        return


    def build_done(self, buildhash):
        if self.nostamp:
            return
        (stampdir, stampfile) = self.stampfile_path()
        if not os.path.exists(stampdir):
            os.makedirs(stampdir)
        with open(stampfile, "w") as _stampfile:
            _stampfile.write(buildhash)
        return


    def build_failed(self):
        return


    def task_cleaned(self):
        hashpath = self.stampfile_path()[1]
        if os.path.exists(hashpath):
            os.remove(hashpath)
