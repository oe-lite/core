import sys
import os

import oelite
import oelite.parse

import ply.lex
import ply.yacc


doclexer = None

__initialized__ = False
if not __initialized__:
    import doclex
    doclexer = ply.lex.lex(module=doclex)
    __initialized__ = True


class DocParser(oelite.parse.oeparse.OEParser):

    def __init__(self, meta=None, parent=None, **kwargs):
        self.body = ""
        self.vars = {}
        self.useflags = {}
        self.inherits = []
        super(DocParser, self).__init__(meta, parent, lexer=doclexer, **kwargs)
        return

    def p_statement_doc_section(self, p):
        '''statement : doc_paragraph NEWLINE'''
        self.body += p[1] + '\n\n'
        return

    def p_doc_asciidoc_par1(self, p):
        '''doc_paragraph : doc_string'''
        p[0] = p[1]
        return

    def p_doc_asciidoc_par3(self, p):
        '''doc_paragraph : doc_paragraph NEWLINE doc_string'''
        p[0] = p[1] + '\n' + p[3]
        return

    def p_doc_string1(self, p):
        '''doc_string : DOCSTRING'''
        p[0] = p[1]
        return

    def p_doc_string2(self, p):
        '''doc_string : doc_string DOCSTRING'''
        p[0] = p[1] + ' ' + p[2]
        return

    # the @var syntax is similar to the doxygen \tparam special command
    # http://www.stack.nl/~dimitri/doxygen/manual/commands.html#cmdtparam
    def p_doc_cmd_var(self, p):
        '''statement : DOCCMDVAR VARNAME doc_paragraph NEWLINE'''
        if self.vars.has_key(p[2]):
            raise oelite.parse.ParseError(
                self, "Variable documentation already defined", p)
        self.vars[p[2]] = p[3]
        return

    # the @useflag syntax is similar to the doxygen \tparam special command
    # http://www.stack.nl/~dimitri/doxygen/manual/commands.html#cmdtparam
    def p_doc_cmd_useflag(self, p):
        '''statement : DOCCMDUSEFLAG VARNAME doc_paragraph NEWLINE'''
        if self.useflags.has_key(p[2]):
            raise oelite.parse.ParseError(
                self, "USE flag documentation already defined", p)
        self.useflags[p[2]] = p[3]
        return

    #Do not continue into (other) oeclass files
    def p_inherit(self, p):
        '''inherit : INHERIT inherit_classes'''
        self.inherits.extend(p[2])
        return

    def docparse(self, filename, title):
        super(DocParser,self).parse(filename)
        return OEliteDocumentation(
            title,
            self.body, self.vars, self.useflags, self.inherits)


class OEliteDocumentation(object):

    def __init__(self, title, body, variables={}, useflags={}, inherits=[]):
        self.title = title
        self.body = body
        self.vars = variables
        self.useflags = useflags
        self.inherits = inherits

    @staticmethod
    def asciidoc_header(title, level='-'):
        return title + '\n' + level*len(title) + '\n\n'

    def get_asciidoc(self):
        text = ''
        if self.body:
            text += self.body + '\n'
        if self.vars:
            text += self.asciidoc_header('Variables')
            for var in sorted(self.vars.keys()):
                text += "%s::\n%s\n"%(var, self.vars[var])
            text += '\n\n'
        if self.useflags:
            text += self.asciidoc_header('USE Flags')
            for useflag in sorted(self.useflags.keys()):
                text += "%s::\n%s\n"%(useflag, self.useflags[useflag])
            text += '\n\n'
        if not text:
            text = 'Seeking documentation writer...\n'
        text = self.asciidoc_header(self.title, level='=') + text
        return text
