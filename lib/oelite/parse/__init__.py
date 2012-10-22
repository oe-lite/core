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

    def __init__(self, parser, msg, details=None, more_details=None):
        self.parser = parser
        self.msg = msg
        self.more_details = more_details
        self.lexer = parser.lexer
        self.errlineno = self.lexer.lineno
        self.details = details

        assert isinstance(self.parser, oelite.parse.oeparse.OEParser)
        assert isinstance(self.msg, basestring)
        assert isinstance(self.lexer, ply.lex.Lexer)

        if "filename" in dir(self.parser):
            self.filename = self.parser.filename
        else:
            self.filename = "<unknown file>",

        if isinstance(self.details, ply.yacc.YaccProduction):
            self.errlineno -= 1
            self.symbol = None
            self.msg += " in %s at line %d"%(
                self.filename, self.errlineno + 1)
        elif isinstance(self.details, ply.lex.LexToken):
            if self.details.type == "error":
                self.symbol = self.details.value[0]
            else:
                self.symbol = self.details.value
            assert isinstance(self.symbol, basestring)
            if self.symbol.endswith("\n"):
                self.errlineno -= 1
            if self.details.type == "error":
                self.msg += " in %s at line %d: %s"%(
                    self.filename, self.errlineno + 1,
                    repr(self.symbol))
            else:
                self.msg += " in %s at line %d: %s %s"%(
                    self.filename, self.errlineno + 1,
                    self.details.type, repr(self.symbol))
        else:
            raise Exception("unsupported details type: %s", type(self.details))

        try:
            self.lines = self.parser.text.splitlines()
        except:
            return

        self.firstline = max(self.errlineno - 5, 0)
        self.lastline = min(self.errlineno + 5, len(self.lines))
        errlinepos = 0
        for lineno in xrange(self.errlineno):
            errlinepos += len(self.lines[lineno]) + 1
        try:
            self.lexpos = self.lexer.lexpos
            errpos = (self.lexpos - 1) - errlinepos
            self.errlinebefore = self.lines[self.errlineno]\
                [:(self.lexpos - errlinepos)]
            self.errlinebefore = len(self.errlinebefore.expandtabs())
            try:
                if self.details.type != "error" and self.symbol != "\n":
                    self.errlinebefore -= len(self.symbol)
            except AttributeError:
                pass
        except AttributeError:
            self.lexpos = None

        return

    def __str__(self):
        return self.msg

    def print_details(self):
        print self.msg

        linenofmtlen = len(str(self.lastline))
        lineprintfmt = "%%s%%%dd %%s"%(linenofmtlen)
        for lineno in xrange(self.firstline, self.lastline):
            if lineno == self.errlineno:
                prefix = "-> "
            else:
                prefix = "   "
            print lineprintfmt%(prefix, lineno + 1,
                                self.lines[lineno].expandtabs())
            if lineno == self.errlineno:
                if not self.symbol:
                    continue
                if self.lexpos is not None:
                    prefixlen = len(prefix) + linenofmtlen + 1
                    print "%s%s"%(" "*(prefixlen + self.errlinebefore),
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

    def __init__(self, parser, filename, p):
        self.filename = filename
        super(FileNotFound, self).__init__(
            parser, "%s not found"%(filename), p)
        return


__all__ = [
    "oelex", "oeparse", "confparse",
    "ParseError", "StatementNotAllowed", "FileNotFound",
    "oelexer",
    ]

import oelex
import oeparse
import confparse
