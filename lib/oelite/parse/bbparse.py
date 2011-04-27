import ply.yacc
import os
import string
import bb.utils
import oelite.parse
from oelite.data.sqlite import SqliteData
from oelite.parse import ParseError, ExpandError
from oelite.parse.bblex import tokens

class BBParser(object):

    def __init__(self, data=None, parent=None):
        self.lexer = oelite.parse.bblexer.clone()
        self.tokens = tokens
        picklefile = "tmp/cache/" + self.__class__.__module__ + ".p"
        self.yacc = ply.yacc.yacc(module=self, debug=0, picklefile=picklefile)
        if data is not None:
            self.data = data
        else:
            self.data = SqliteData()
        self.parent = parent
        return


    def setData(self, data):
        self.data = data
        return


    def lextest(self, data, debug=False):
        self.lexer.input(data)
        tokens = []
        for tok in self.lexer:
            if debug:
                print tok.type, repr(tok.value), tok.lineno, tok.lexpos
            tokens.append((tok.type, tok.value))
        return tokens


    start = 'syntax'


    def p_syntax(self, p):
        '''syntax : statement
                  | statement syntax'''
        return

    def p_statement(self, p):
        '''statement : NEWLINE
                     | assignment NEWLINE
                     | export_variable NEWLINE
                     | include NEWLINE
                     | require NEWLINE
                     | inherit NEWLINE
                     | func NEWLINE
                     | fakeroot_func NEWLINE
                     | python_func NEWLINE
                     | def_func
                     | addtask NEWLINE
                     | addhook NEWLINE
                     | COMMENT'''
        return

    def p_variable(self, p):
        '''variable : VARNAME
                    | export_variable'''
        p[0] = p[1]
        return

    def p_export_variable(self, p):
        '''export_variable : EXPORT VARNAME'''
        self.data.setVarFlag(p[2], "export", "1")
        p[0] = p[2]
        return

    def p_flag(self, p):
        '''varflag : VARNAME FLAG'''
        p[0] = (p[1], p[2])
        return

    def p_simple_var_assignment(self, p):
        '''assignment : variable ASSIGN STRING'''
        self.data.setVar(p[1], p[3])
        return

    def p_simple_flag_assignment(self, p):
        '''assignment : varflag ASSIGN STRING'''
        self.data.setVarFlag(p[1][0], p[1][1], p[3])
        return

    def p_exp_var_assignment(self, p):
        '''assignment : variable EXPASSIGN STRING'''
        self.data.setVar(p[1], self.data.expand(p[3]))
        return

    def p_exp_flag_assignment(self, p):
        '''assignment : varflag EXPASSIGN STRING'''
        self.data.setVarFlag(p[1][0], p[1][1], self.data.expand(p[3]))
        return

    def p_defaultval_assignment(self, p):
        '''assignment : variable LAZYASSIGN STRING'''
        self.data.setVar(p[1], "defaultval", p[3])
        return

    def p_weak_var_assignment(self, p):
        '''assignment : variable WEAKASSIGN STRING'''
        if not p[1] in self.data:
            self.data.setVar(p[1], p[3])
        return

    def p_weak_flag_assignment(self, p):
        '''assignment : varflag WEAKASSIGN STRING'''
        if self.data.getVarFlag(p[1][0], p[1][1]) == None:
            self.data.setVarFlag(p[1][0], p[1][1], p[3])
        return

    def p_append_var_assignment(self, p):
        '''assignment : variable APPEND STRING'''
        self.data.appendVar(p[1], p[3], separator=" ")
        return

    def p_append_flag_assignment(self, p):
        '''assignment : varflag APPEND STRING'''
        self.data.appendVarFlag(p[1][0], p[1][1], p[3], separator=" ")
        return

    def p_prepend_var_assignment(self, p):
        '''assignment : variable PREPEND STRING'''
        self.data.prependVar(p[1], p[3], separator=" ")
        return

    def p_prepend_flag_assignment(self, p):
        '''assignment : varflag PREPEND STRING'''
        self.data.prependVarFlag(p[1][0], p[1][1], p[3], separator=" ")
        return

    def p_predot_var_assignment(self, p):
        '''assignment : variable PREDOT STRING'''
        self.data.appendVar(p[1], p[3])
        return

    def p_predot_flag_assignment(self, p):
        '''assignment : varflag PREDOT STRING'''
        self.data.appendVarFlag(p[1][0], p[1][1], p[3])
        return

    def p_postdot_var_assignment(self, p):
        '''assignment : variable POSTDOT STRING'''
        self.data.prependVar(p[1], p[3])
        return

    def p_postdot_flag_assignment(self, p):
        '''assignment : varflag POSTDOT STRING'''
        self.data.prependVarFlag(p[1][0], p[1][1], p[3])
        return

    def p_include(self, p):
        '''include : INCLUDE INCLUDEFILE'''
        self.include(p[2])
        return

    def p_require(self, p):
        '''require : REQUIRE INCLUDEFILE'''
        self.include(p[2], require=True)
        return

    def p_inherit(self, p):
        '''inherit : INHERIT inherit_classes'''
        for inherit_class in p[2]:
            self.inherit(inherit_class)
        return

    def p_inherit_classes(self, p):
        '''inherit_classes : INHERITCLASS'''
        p[0] = [ p[1] ]
        return

    def p_inherit_classes2(self, p):
        '''inherit_classes : INHERITCLASS inherit_classes'''
        p[0] = [ p[1] ] + p[2]
        return

    def p_addtask(self, p):
        '''addtask : addtask_task'''
        self.data.setVarFlag(p[1], "task", True)
        #print "addtask %s"%(p[1])
        return

    def p_addtask_w_dependencies(self, p):
        '''addtask : addtask_task addtask_dependencies'''
        self.p_addtask(p)
        self.data.appendVarFlag(p[1], "deps", " ".join(p[2][0]), " ")
        for before_task in p[2][1]:
            self.data.appendVarFlag(before_task, "deps", p[1], " ")
        return

    def taskname(self, s):
        if not s.startswith("do_"):
            return "do_" + s
        return s

    def p_addtask_task(self, p):
        '''addtask_task : ADDTASK TASK'''
        p[0] = self.taskname(p[2])
        return

    def p_addtask_dependencies1(self, p):
        '''addtask_dependencies : addtask_dependency'''
        p[0] = p[1]
        return

    def p_addtask_dependencies2(self, p):
        '''addtask_dependencies : addtask_dependency addtask_dependencies'''
        p[0] = (set(p[1][0] + p[2][0]), set(p[1][1] + p[2][1]))
        return

    def p_addtask_dependency(self, p):
        '''addtask_dependency : addtask_after
                              | addtask_before'''
        p[0] = p[1]
        return

    def p_addtask_after(self, p):
        '''addtask_after : AFTER tasks'''
        p[0] = (p[2], [])
        return

    def p_addtask_before(self, p):
        '''addtask_before : BEFORE tasks'''
        p[0] = ([], p[2])
        return

    def p_tasks(self, p):
        '''tasks : TASK'''
        p[0] = [ self.taskname(p[1]) ]
        return

    def p_tasks2(self, p):
        '''tasks : TASK tasks'''
        p[0] = [ self.taskname(p[1]) ] + p[2]
        return


    def p_addhook1(self, p):
        '''addhook : ADDHOOK HOOK TO HOOKNAME'''
        self.data.add_hook(p[4], p[2])
        return

    def p_addhook2(self, p):
        '''addhook : ADDHOOK HOOK TO HOOKNAME HOOKSEQUENCE'''
        self.data.add_hook(p[4], p[2], p[5])
        return

    def p_addhook3(self, p):
        '''addhook : ADDHOOK HOOK TO HOOKNAME addhook_dependencies'''
        self.data.add_hook(p[4], p[2], after=p[5][0], before=p[5][1])
        return

    def p_addhook4(self, p):
        '''addhook : ADDHOOK HOOK TO HOOKNAME HOOKSEQUENCE addhook_dependencies'''
        self.data.add_hook(p[4], p[2], p[5], after=p[6][0], before=p[6][1])
        return

    def p_addhook_dependencies1(self, p):
        '''addhook_dependencies : addhook_dependency'''
        p[0] = p[1]
        return

    def p_addhook_dependencies2(self, p):
        '''addhook_dependencies : addhook_dependency addhook_dependencies'''
        p[0] = (set(p[1][0] + p[2][0]), set(p[1][1] + p[2][1]))
        return

    def p_addhook_dependency(self, p):
        '''addhook_dependency : addhook_after
                              | addhook_before'''
        p[0] = p[1]
        return

    def p_addhook_after(self, p):
        '''addhook_after : AFTER hooks'''
        p[0] = (p[2], [])
        return

    def p_addhook_before(self, p):
        '''addhook_before : BEFORE hooks'''
        p[0] = ([], p[2])
        return

    def p_hooks(self, p):
        '''hooks : HOOK'''
        p[0] = [ p[1] ]
        return

    def p_hooks2(self, p):
        '''hooks : HOOK hooks'''
        p[0] = [ p[1] ] + p[2]
        return


    # function related flags:
    #  python = BOOL
    #  args = STRING
    #  bash = BOOL
    #  fakeroot = BOOL

    # other flags
    #  export = BOOL or list of tasks    export to shell function
    #  defaultval = STRING  (default value assigned)
    #  export_func ???
    #  task = BOOL
    #  before = [ TASK ... ]
    #  after = [ TASK ... ]

    def p_func(self, p):
        '''func : VARNAME FUNCSTART func_body FUNCSTOP'''
        self.data.setVar(p[1], p[3])
        self.data.setVarFlag(p[1], "bash", True)
        p[0] = p[1]
        return

    def p_func_body(self, p):
        '''func_body : FUNCLINE'''
        p[0] = p[1]
        return

    def p_func_body2(self, p):
        '''func_body : FUNCLINE func_body'''
        p[0] = p[1] + p[2]
        return

    def p_fakeroot_func(self, p):
        '''fakeroot_func : FAKEROOT func'''
        self.data.setVarFlag(p[2], "fakeroot", True)
        p[0] = p[2]
        return

    def p_python_func(self, p):
        '''python_func : PYTHON VARNAME FUNCSTART func_body FUNCSTOP'''
        self.data.setVar(p[2], p[4])
        self.data.setVarFlag(p[2], "python", True)
        p[0] = p[2]
        return

    def p_python_anonfunc(self, p):
        '''python_func : PYTHON FUNCSTART func_body FUNCSTOP'''
        #funcname = "__anon_%s_%d"%(self.filename.translate(
        #        string.maketrans('/.+-', '____')), p.lexer.funcstart + 1)
        funcname = "__%s_%d__"%(
            self.filename.translate(string.maketrans('/+-.', '____')),
            p.lexer.funcstart + 1)
        #print "anonymous python %s"%(funcname)
        #self.data.addAnonymousFunction(self.filename, p.lexer.funcstart + 1,
        #                               p[3])
        self.data.setVar(funcname, p[3])
        self.data.setVarFlag(funcname, 'python', True)
        self.data.setVarFlag(funcname, 'args', "d")
        self.data.add_hook("post_recipe_parse", funcname)
        return

    def p_def_func(self, p):
        '''def_func : DEF VARNAME def_funcargs NEWLINE func_body
                    | DEF VARNAME def_funcargs NEWLINE func_body FUNCSTOP'''
        self.data.setVar(p[2], p[5])
        self.data.setVarFlag(p[2], "python", True)
        if p[3]:
            self.data.setVarFlag(p[2], "args", p[3])
        self.data.setVarFlag(p[2], "autoimport", True)
        return

    def p_def_args1(self, p):
        '''def_funcargs : ARGSTART STRING ARGSTOP'''
        p[0] = p[2]
        return

    def p_def_args2(self, p):
        '''def_funcargs : ARGSTART ARGSTOP'''
        p[0] = None
        return

    def p_error(self, p):
        raise ParseError(self, "Syntax error", p)


    def inherit(self, filename):
        if not os.path.isabs(filename) and not filename.endswith(".bbclass"):
            filename = os.path.join("classes", "%s.bbclass"%(filename))
        if not "__INHERITS" in self.data:
            self.data["__INHERITS"] = filename
        else:
            __INHERITS = self.data["__INHERITS"]
            if filename in __INHERITS.split():
                return
            self.data.appendVar("__INHERITS", filename)
        self.include(filename, require=True)


    def include(self, filename, require=False):
        try:
            filename = self.data.expand(filename)
        except ExpandError, e:
            raise ParseError(self, str(e), self, lineno=(self.lexer.lineno - 1))
        #print "including file=%s"%(filename)
        parser = self.__class__(self.data, parent=self)
        rv = parser.parse(filename, require, parser)
        return rv


    def parse(self, filename, require=True, parser=None):
        #print "parsing %s"%(filename)
        if not os.path.isabs(filename):
            bbpath = self.data.getVar("BBPATH")
            if self.parent:
                dirname = os.path.dirname(self.parent.filename)
                bbpath = "%s:%s"%(dirname, bbpath)
            filename = bb.utils.which(bbpath, filename)
        else:
            if not os.path.exists(filename):
                print "file not found: %s"%(filename)
                return

        if filename:
            self.filename = os.path.realpath(filename)
        else:
            self.filename = ""

        if not os.path.exists(self.filename):
            if not require:
                return
            else:
                print "required file could not be included: %s"%(self.filename)
                return

        if self.parent:
            oldfile = os.path.realpath(self.filename[-1])
            if self.filename == oldfile:
                print "don't include yourself!"
                return

        if parser is None and not filename.endswith(".bbclass"):
            self.data.setVar("FILE", filename)
            self.data.setVar("FILE_DIRNAME", os.path.dirname(filename))
            if filename.endswith(".bb"):
                file_split = os.path.basename(filename[:-3]).split("_")
                if len(file_split) > 3:
                    raise Exception("Invalid recipe filename: %s"%(filename))
                self.data.setVar("PN", file_split[0])
                if len(file_split) > 1:
                    self.data.setVar("PV", file_split[1])
                if len(file_split) > 2:
                    self.data.setVar("PR", file_split[2])

        mtime = os.path.getmtime(self.filename)
        f = open(self.filename)
        self.text = f.read()
        f.close()
        self.data.setFileMtime(self.filename, mtime)

        if not parser:
            parser = self
        return parser._parse(self.text)


    def _parse(self, s):
        self.lexer.lineno = 0
        self.yacc.parse(s + '\n', lexer=self.lexer)
        return self.data


    def yacctest(self, s):
        self.data = SqliteData()
        return self._parse(s)
