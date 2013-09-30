from oelex import *

tokens += ['DOCSTRING']

doc_special_commands = {
    'var'          : 'DOCCMDVAR',
    'useflag'      : 'DOCCMDUSEFLAG',
}

tokens += list(doc_special_commands.values())

states = states + (
    ('doc', 'exclusive'),
    ('docvar', 'exclusive'),
    )

def t_DOC(t):
    r'\#{2,}'
    t.lexer.push_state("doc")
    return

t_doc_ignore = ' \t'

def t_doc_NEWLINE(t):
    r'\n'
    t.lexer.lineno += 1
    t.lexer.pop_state()
    return t

#make it possible to write @ in docs
def t_doc_DOCCMDESC(t):
    r'\\@'
    t.type = "DOCSTRING"
    t.value = "@"
    return t

def t_doc_DOCCMD(t):
    r'@[^ \t]+'
    try:
        t.type = doc_special_commands[t.value[1:]]
    except KeyError:
        raise oelite.parse.ParseError(t.lexer.parser, "Unknown doc command", t)
    if t.value[1:] in ('var', 'useflag'):
        t.lexer.push_state('docvar')
    return t

def t_doc_DOCSTRING(t):
    r'[^\n]+'
    t.type = "DOCSTRING"
    return t

t_docvar_ignore = ' \t'

def t_docvar_VARNAME(t):
    r'[a-zA-Z_][a-zA-Z0-9_\-\${}\+\.]*'
    t.type = "VARNAME"
    t.lexer.pop_state()
    return t

def t_docvar_NEWLINE(t):
    r'\n'
    t.lexer.lineno += 1
    t.lexer.pop_state()
    t.lexer.pop_state()
    return t
