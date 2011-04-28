import ply.lex

__all__ = [
#    'expandparse',
    'confparse', 'bbparse',
    'ParseError', #'ExpandError',
    'bblexer', #'expandlexer',
    ]


bblexer = None
#expandlexer = None

def init():
    import oelite.parse.bblex
    global bblexer
    bblexer = ply.lex.lex(module=oelite.parse.bblex)
    #import oelite.parse.expandlex
    #global expandlexer
    #expandlexer = ply.lex.lex(module=oelite.parse.expandlex)
    return


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

    def __init__(self, parser, msg, details=None, symbol=None, lineno=None):
        self.parser = parser
        self.msg = msg
        self.details = details
        if lineno is not None:
            self.errlineno = lineno
        elif "lexer" in dir(self.details):
            self.errlineno = self.details.lexer.lineno
        else:
            self.errlineno = self.details.lineno
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
        try:
            self.lexer = self.details.lexer
        except:
            self.lexer = self.parser.lexer
        if not self.symbol:
            self.msg += " in %s at line %d"%(
                parser.filename or "<unknown file>",
                self.lexer.lineno + 1)
        elif self.details.type == "error":
            self.msg += " in %s at line %d: %s"%(
                parser.filename or "<unknown file>",
                self.lexer.lineno + 1,
                repr(self.symbol))
        else:
            self.msg += " in %s at line %d: %s %s"%(
                parser.filename or "<unknown file>",
                self.lexer.lineno + 1,
                self.details.type, repr(self.symbol))
        return

    def __str__(self):
        return self.msg

    def print_details(self):
        print self.msg
        if not self.details:
            return ""
        lines = self.parser.text.splitlines()
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
            lexpos = self.details.lexpos
            errpos = (lexpos - 1) - errlinepos
            errlinebefore = lines[self.errlineno]\
                [:(lexpos - errlinepos)]
            errlinebefore = len(errlinebefore.expandtabs())
        except AttributeError:
            lexpos = None
        linenofmtlen = len(str(lastline))
        lineprintfmt = "%%s%%%dd %%s"%(linenofmtlen)
        for lineno in xrange(firstline, lastline):
            if lineno == self.errlineno:
                if lineno:
                    print ""
                prefix = "-> "
            else:
                prefix = "   "
            print lineprintfmt%(prefix, lineno + 1,
                                lines[lineno].expandtabs())
            if lineno == self.errlineno:
                if lexpos:
                    prefixlen = len(prefix) + linenofmtlen + 1
                    print "%s%s"%(" "*(prefixlen + errlinebefore),
                                  "^"*len(self.symbol))
                else:
                    print ""
        if self.parser.parent:
            parent = self.parser.parent
            print "Included from %s"%(parent.filename)
            parent = parent.parent
            while parent:
                print "              %s"%(parent.filename)
        return


