import ply.lex
import oelite.parse.oeparse


oelexer = None

__initialized__ = False
if not __initialized__:
    import oelex
    oelexer = ply.lex.lex(module=oelex)
    __initialized__ = True


class ExpandError(Exception):
    def __init__(self, parser, msg):
        self.parser = parser
        self.msg = msg
        return

    def __repr__(self):
        return "ExpandError(%s)"%(repr(self.msg))

    def __str__(self):
        return "Variable expansion error: %s"%(self.msg)


class ParseError(Exception):

    def __init__(self, parser, msg, details=None, symbol=None, lineno=None,
                 more_details=None):
        """
        parser = OEParser instance
        msg = string
        details = 
        """
        assert isinstance(parser, oelite.parse.oeparse.OEParser)
        assert isinstance(msg, basestring)

        self.parser = parser
        self.msg = msg
        self.more_details = more_details
        try:
            self.lexer = details.lexer
        except:
            self.lexer = parser.lexer
        #print "parser=%s"%(parser)
        #print dir(self.parser)
        #print dir(self.parser.lexer)
        #print "lineno arg", lineno
        #print "lineno", self.parser.lexer.lineno
        if not self.parser and "parser" in dir(self.lexer):
        #if not self.parser:
            self.parser = self.lexer.parser
        if details:
            self.details = details
        elif "yacc" in dir(self.parser) and "lexer" in dir(self.parser.yacc):
            self.details = self.parser.yacc.lexer
        elif self.parser and "lexer" in dir(self.parser):
            self.details = self.parser.lexer
        else:
            self.details = None
        if lineno is not None:
            self.errlineno = lineno
        elif "lexer" in dir(self.parser) and "lineno" in dir(self.parser.lexer):
            self.errlineno = self.parser.lexer.lineno
        elif "details" in self and "lexer" in dir(self.details):
            self.errlineno = self.details.lexer.lineno
        elif "details" in self and "lineno" in dir(self.details):
            self.errlineno = self.details.lineno
        else:
            # FIXME: try harder to get a proper errlineno
            self.errlineno = 0
        if symbol:
            self.symbol = symbol
        #elif self.details is None:
        #    self.symbol = ""
        elif not "value" in dir(self.details):
            self.symbol = None
        elif self.details.type == "error":
            self.symbol = self.details.value[0]
        else:
            self.symbol = self.details.value
        if isinstance(self.symbol, basestring) and self.symbol.endswith("\n"):
            # FIXME: is this always correct?
            self.errlineno -= 1
        if "filename" in dir(self.parser):
            self.filename = self.parser.filename
        elif not self.filename:
            self.filename = "<unknown file>",
        #if isinstance(self.parser, oelite.parse.oeparse.OEParser):
        #    self.parser = parser.yacc
        if not self.symbol:
            self.msg += " in %s at line %d"%(
                self.filename, self.errlineno + 1)
        elif self.details.type == "error":
            self.msg += " in %s at line %d: %s"%(
                self.filename, self.errlineno + 1,
                repr(self.symbol))
        else:
            self.msg += " in %s at line %d: %s %s"%(
                self.filename, self.errlineno + 1,
                self.details.type, repr(self.symbol))
        return

    def __str__(self):
        return self.msg

    def print_details(self):
        print self.msg
        if not self.details:
            return ""
        if "text" in dir(self.parser):
            lines = self.parser.text.splitlines()
        elif "yacc" in dir(self.parser) and "text" in dir(self.parser.yacc):
            lines = self.parser.yacc.text.splitlines()
        else:
            print type(self.lexer.lexdata)
            lines = self.lexer.lexdata.splitlines()
        #errlineno = self.details.lineno
        #errlineno = self.lexer.lineno
        firstline = max(self.errlineno - 5, 0)
        lastline = min(self.errlineno + 5, len(lines))
        errlinepos = 0
        for lineno in xrange(self.errlineno):
            errlinepos += len(lines[lineno]) + 1
        #if isinstance(self.details, ply.lex.LexToken):
        #    print "this is a LexToken"
        #    lexpos = self.details.lexpos
        #elif isinstance(self.details, ply.lex.Lexer):
        #    print "this is a Lexer"
        #    lexpos = self.details.lexpos - len(self.symbol)
        try:
            #lexpos = self.details.lexpos
            lexpos = self.lexer.lexpos
            errpos = (lexpos - 1) - errlinepos
            errlinebefore = lines[self.errlineno]\
                [:(lexpos - errlinepos)]
            errlinebefore = len(errlinebefore.expandtabs())
            try:
                if self.symbol == self.details.value:
                    errlinebefore -= len(self.symbol)
            except AttributeError:
                pass
        except AttributeError:
            lexpos = None
        linenofmtlen = len(str(lastline))
        lineprintfmt = "%%s%%%dd %%s"%(linenofmtlen)
        for lineno in xrange(firstline, lastline):
            if lineno == self.errlineno:
                #print ""
                prefix = "-> "
            else:
                prefix = "   "
            print lineprintfmt%(prefix, lineno + 1,
                                lines[lineno].expandtabs())
            if lineno == self.errlineno:
                if lexpos:
                    prefixlen = len(prefix) + linenofmtlen + 1
                    print "%s%s"%(" "*(prefixlen + errlinebefore),
                                  "^"*len(self.symbol or ""))
                else:
                    print ""
        if self.parser.parent:
            parent = self.parser.parent
            print "Included from %s"%(parent.filename)
            parent = parent.parent
            while parent:
                print "              %s"%(parent.filename)
                parent = parent.parent
        if self.more_details:
            if "print_details" in dir(self.more_details):
                self.more_details.print_details()
            else:
                print self.more_details
        return


class StatementNotAllowed(ParseError):

    def __init(self, parser, p, statement):
        super(StatementNotAllowedInConf, self).__init__(
            parser, "%s statement not allowed"%(statement), p)
        return


class FileNotFound(ParseError):

    def __init__(self, parser, filename, p, lineno=None):
        self.filename = filename
        super(FileNotFound, self).__init__(
            parser, "%s not found"%(filename), p, lineno=lineno)
        return


__all__ = [
    "oelex", "oeparse", "confparse",
    "ParseError", "StatementNotAllowed", "FileNotFound",
    "oelexer",
    ]

import oelex
import oeparse
import confparse
