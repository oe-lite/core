import ply.yacc
import re
import bb.utils
import oelite.pyexec
from oelite.parse import ExpandError
from oelite.parse.expandlex import tokens
import oelite.meta

class ExpandParser(object):

    def __init__(self, data, allow_unexpand=False):
        self.lexer = oelite.parse.expandlexer.clone()
        self.tokens = tokens
        picklefile = "tmp/cache/" + self.__class__.__module__ + ".p"
        self.yacc = ply.yacc.yacc(module=self, debug=0, picklefile=picklefile)
        self.data = data
        self.allow_unexpand = allow_unexpand
        return


    def set_data(self, data):
        self.data = data
        return

    def set_allow_unexpand(self, allow_unexpand):
        self.allow_unexpand = allow_unexpand
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

    def p_syntax1(self, p):
        '''syntax : string'''
        p[0] = str(p[1])
        return

    def p_syntax2(self, p):
        '''syntax : string syntax'''
        p[0] = str(p[1]) + p[2]
        return

    def p_string(self, p):
        '''string : chars
                  | variable
                  | python'''
        p[0] = p[1]
        return

    def p_chars1(self, p):
        '''chars : CHARS'''
        p[0] = p[1]
        return

    def p_chars2(self, p):
        '''chars : CHARS chars'''
        p[0] = p[1] + p[2]
        return

    def p_variable(self, p):
        '''variable : VAROPEN varname VARCLOSE'''
        #print "expanding %s"%(p[2])
        #print "allow_unexpand=%s"%(self.allow_unexpand)
        if self.allow_unexpand:
            expand = 2
        else:
            expand = 1
        val = self.data.getVar(p[2], expand)
        if val == None:
            if self.allow_unexpand:
                p[0] = "${" + varname + "}"
            else:
                raise ExpandError(self, "Unknown variable: %s"%(p[2]))
        else:
            p[0] = val
        return

    def p_varname1(self, p):
        '''varname : varnamepart'''
        p[0] = p[1]
        return

    def p_varname2(self, p):
        '''varname : varnamepart varname'''
        p[0] = p[1] + p[2]
        return

    def p_varnamepart1(self, p):
        '''varnamepart : VARNAME'''
        p[0] = p[1]
        return

    def p_varnamepart2(self, p):
        '''varnamepart : variable'''
        if not re.match(self.t_var_VARNAME.__doc__ + '$', p[1]):
            raise ValueError(p[1])
        p[0] = p[1]
        return

    def p_python(self, p):
        '''python : PYTHONOPEN syntax PYTHONCLOSE'''
        print "python code: %s"%(repr(p[2]))
        try:
            val = oelite.pyexec.inlineeval(p[2], self.data)
            p[0] = self.data.expand(val, self.allow_unexpand)
        except NameError, e:
            raise ExpandError(self, "Python exception while expanding: %s\n%s"%(p[2], e))
        #print "python code done"
        return


    def p_error(self, p):
        raise ExpandError(p, "unknown error")


    def yacctest(self, s):
        self.data = oelite.meta.DictMeta()
        self.parse(s)
        return self.data


    def expand(self, s):
        if s.startswith("oe.path "):
            raise Exception("Aiee")
        #print "s=%s lexer=%s"%(repr(s), repr(self.lexer))
        return self.yacc.parse(s, lexer=self.lexer)
