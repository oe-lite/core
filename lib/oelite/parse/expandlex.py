tokens = (
    'CHARS',
    'VAROPEN', 'VARNAME', 'VARCLOSE',
    'PYTHONOPEN', 'PYTHONCLOSE',
    )

states = (
    ('var', 'exclusive'),
    ('python', 'exclusive'),
    )

precedence = ()

literals = ''


def t_INITIAL_var_PYTHONOPEN(t):
    r'\${@'
    #print "push_state python"
    t.lexer.push_state('python')
    return t

def t_ANY_VAROPEN(t):
    r'\${'
    #print "push_state var"
    t.lexer.push_state('var')
    return t


def t_python_PYTHONCLOSE(t):
    r'}'
    #print "pop_state python"
    t.lexer.pop_state()
    return t


def t_var_VARCLOSE(t):
    r'}'
    #print "pop_state var"
    t.lexer.pop_state()
    return t

def t_var_VARNAME(t):
    r'[a-zA-Z_][a-zA-Z0-9_]*'
    return t


def t_INITIAL_python_CHARS(t):
    #r'([^\$]|\\\$)+'
    r'[^\\\$}]+'
    return t

def t_INITIAL_python_SPECIALCHAR(t):
    r'\\\$}'
    t.type = 'CHARS'
    return t


def t_ANY_error(t):
    from oelite.parse import ExpandError
    raise ExpandError(t.lexer, "Illegal character %s"%(repr(t.value[0])))

t_ANY_ignore = ''
