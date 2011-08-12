import oelite.parse
from oelite.parse.oeparse import OEParser

import ply.lex
import ply.yacc

class ConfParser(OEParser):

    def __init__(self, data=None, parent=None, **kwargs):
        super(ConfParser, self).__init__(data, parent, **kwargs)
        return


    # Override inherit statements

    def p_inherit(self, p):
        '''inherit : INHERIT inherit_classes'''
        raise StatementNotAllowed(self, p, "inherit")


    # Override addtask statements

    def p_addtask(self, p):
        '''addtask : addtask_task'''
        raise StatementNotAllowed(self, p, "addtask")

    def p_addtask_w_dependencies(self, p):
        '''addtask : addtask_task addtask_dependencies'''
        raise StatementNotAllowed(self, p, "addtask")


    # Override function definitions

    #def p_def_func(self, p):
    #    '''def_func : DEF VARNAME def_funcargs NEWLINE func_body
    #                | DEF VARNAME def_funcargs NEWLINE func_body FUNCSTOP'''
    #    raise StatementNotAllowed(self, p, "def function")
    #
    #def p_func(self, p):
    #    '''func : VARNAME FUNCSTART func_body FUNCSTOP'''
    #    raise StatementNotAllowed(self, p, "function")

    def p_python_anonfunc(self, p):
        '''python_func : PYTHON FUNCSTART func_body FUNCSTOP'''
        raise StatementNotAllowed(self, p, "anonymous function")
