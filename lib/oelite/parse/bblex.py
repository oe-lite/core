tokens = [
    'VARNAME', 'FLAG',
    'ASSIGN', 'EXPASSIGN', 'WEAKASSIGN', 'LAZYASSIGN',
    'APPEND', 'PREPEND', 'POSTDOT', 'PREDOT',
    'STRING',
    'NEWLINE', 'COMMENT',
    'INCLUDEFILE', # 'INCLUDE' and 'REQUIRE' included as reserved word
    'INHERITCLASS', # 'INHERIT' included as reserved word
    'FUNCSTART', 'FUNCSTOP', 'FUNCLINE', 'ARGSTART', 'ARGSTOP',
    'TASK',
    ]

reserved = {
    'export'	: 'EXPORT',
    'require'	: 'REQUIRE',
    'include'	: 'INCLUDE',
    'inherit'	: 'INHERIT',
    'fakeroot'	: 'FAKEROOT',
    'python'	: 'PYTHON',
    'addtask'	: 'ADDTASK',
    'addhook'	: 'ADDHOOK',
    'def'	: 'DEF',
    }
tokens += list(reserved.values())

states = (
    ('assign', 'exclusive'),
    ('def', 'exclusive'),
    ('defargs', 'exclusive'),
    ('defbody', 'exclusive'),
    ('func', 'exclusive'),
    ('include', 'exclusive'),
    ('inherit', 'exclusive'),
    ('addtask', 'exclusive'),
    ('addhook', 'exclusive'),
    )

precedence = ()

literals = ''


t_ignore = ' \t'

def t_VARNAME(t):
    r'[a-zA-Z_][a-zA-Z0-9_\-\${}/\+\.]*'
    t.type = reserved.get(t.value, 'VARNAME')
    if t.type == 'VARNAME':
        pass
    elif t.type in ('INCLUDE', 'INHERIT', 'ADDTASK', 'ADDHOOK', 'DEF'):
        t.lexer.push_state(t.value)
    elif t.type == 'REQUIRE':
        t.lexer.push_state('include')
    #print "VARNAME %s %s"%(t.type, t.value)
    return t

def t_FLAG(t):
    r'\[[a-zA-Z_][a-zA-Z0-9_]*\]'
    t.type = reserved.get(t.value, 'FLAG')
    t.value = t.value[1:-1]
    return t

def t_APPEND(t):
    r'\+='
    t.lexer.push_state("assign")
    return t

def t_PREDOT(t):
    r'\.='
    t.lexer.push_state("assign")
    return t

def t_LAZYASSIGN(t):
    r'\?\?='
    t.lexer.push_state("assign")
    return t

def t_WEAKASSIGN(t):
    r'\?='
    t.lexer.push_state("assign")
    return t

def t_EXPASSIGN(t):
    r':='
    t.lexer.push_state("assign")
    return t

def t_PREPEND(t):
    r'=\+'
    t.lexer.push_state("assign")
    return t

def t_POSTDOT(t):
    r'=\.'
    t.lexer.push_state("assign")
    return t

def t_ASSIGN(t):
    r'='
    t.lexer.push_state("assign")
    return t

def t_COMMENT(t):
    r'\#[^\n]*'
    pass # no return value, token discarded

def t_NEWLINE(t):
    r'\n+'
    t.lexer.lineno += len(t.value)
    return t


t_def_ignore = ' \t'

def t_def_FUNCSTART(t):
    r'[a-zA-Z_][a-zA-Z0-9_]*'
    t.type = "VARNAME"
    return t

def t_def_ARGSTART(t):
    r'\('
    t.type = "ARGSTART"
    t.lexer.push_state('defargs')
    return t

def t_def_NEWLINE(t):
    r'\n'
    t.lexer.lineno += 1
    t.lexer.push_state('defbody')
    return t

t_defargs_ignore = ''

def t_defargs_ARGS(t):
    r'[^:\(\)]+'
    t.type = "STRING"
    return t

def t_defargs_ARGSTOP(t):
    r'\)[ \t]*:[ \t]*'
    t.lexer.pop_state()
    return t

t_defbody_ignore = ''

def t_defbody_FUNCSTOP(t):
    r'\S'
    t.lexer.lexpos -= 1
    t.lexer.pop_state()
    t.lexer.pop_state()
    return t

def t_defbody_FUNCLINE(t):
    r'[^\n]*\n'
    t.lexer.lineno += 1
    return t

def t_defbody_LASTFUNCLINE(t):
    r'[^\n]+'
    t.lexer.lineno += 1
    t.type = "FUNCLINE"
    return t


t_include_ignore = ' \t'

def t_include_INCLUDEFILE(t):
    r'\S+'
    return t

def t_include_NEWLINE(t):
    r'\n'
    t.lexer.lineno += 1
    t.lexer.pop_state()
    return t


t_inherit_ignore = ' \t'

def t_inherit_INHERITCLASS(t):
    r'\S+'
    return t

def t_inherit_NEWLINE(t):
    r'\n'
    t.lexer.lineno += 1
    t.lexer.pop_state()
    return t


def t_FUNCSTART(t):
    r'\(\)[ \t]*\{[ \t]*\n'
    t.lexer.funcstart = t.lexer.lineno
    t.lexer.push_state('func')
    t.lexer.lineno += 1
    return t

t_func_ignore = ""

def t_func_FUNCSTOP(t):
    r'\}'
    t.lexer.pop_state()
    return t

def t_func_FUNCLINE(t):
    r'[^\n]*\n'
    t.lexer.lineno += 1
    return t


t_addtask_ignore = ' \t'

addtask_reserved = {
    'after'	: 'AFTER',
    'before'	: 'BEFORE',
    }
tokens += list(addtask_reserved.values())

def t_addtask_TASK(t):
    r'[a-zA-Z_]+'
    t.type = addtask_reserved.get(t.value, 'TASK')
    return t

def t_addtask_NEWLINE(t):
    r'\n'
    t.lexer.lineno += 1
    t.lexer.pop_state()
    return t


t_addhook_ignore = ' \t'

tokens.append('HOOK')

addhook_reserved = {
    'to'	: 'TO',
    'after'	: 'AFTER',
    'before'	: 'BEFORE',
    }
tokens += list(addhook_reserved.values())

addhook_hooknames = [
    'post_conf_parse',
    'post_recipe_parse',
    ]
tokens.append('HOOKNAME')

addhook_sequencenames = [
    'first',
    'middle',
    'last',
    ]
tokens.append('HOOKSEQUENCE')

def t_addhook_NAME(t):
    r'[a-zA-Z][a-zA-Z0-9_]*'
    if t.value in addhook_hooknames:
        t.type = 'HOOKNAME'
        return t
    if t.value in addhook_sequencenames:
        t.type = 'HOOKSEQUENCE'
        t.value = addhook_sequencenames.index(t.value)
        return t
    t.type = addhook_reserved.get(t.value, 'HOOK')
    return t

def t_addhook_NEWLINE(t):
    r'\n'
    t.lexer.lineno += 1
    t.lexer.pop_state()
    return t


t_assign_ignore = ' \t'

def t_assign_TRUE(t):
    r'True'
    t.type = "STRING"
    t.value = "1"
    t.lexer.pop_state()
    return t

def t_assign_FALSE(t):
    r'False'
    t.type = "STRING"
    t.value = "0"
    t.lexer.pop_state()
    return t

def t_assign_NUMBER(t):
    r'\d+'
    t.type = "STRING"
    t.lexer.pop_state()
    return t

def t_assign_EMPTYSTRING(t):
    r'""|\'\''
    t.type = "STRING"
    t.value = ""
    t.lexer.pop_state()
    return t

def t_assign_DQUOTESTRING(t):
    r'"(\\"|\\\n|[^"\n])*?"'
    t.type = "STRING"
    t.lexer.lineno += t.value.count('\n')
    t.value = t.value[1:-1].replace('\\\n','').replace('\\"','"')
    t.lexer.pop_state()
    return t

def t_assign_SQUOTESTRING(t):
    r"'(\\'|\\\n|[^'\n])*?'"
    t.type = "STRING"
    t.lexer.lineno += t.value.count('\n')
    t.value = t.value[1:-1].replace('\\\n','').replace("\\'","'")
    t.lexer.pop_state()
    return t

def t_assign_UNTERMINATEDDQUOTESTRING(t):
    r'"(\\"|\\\n|[^"\n])*?\n'
    t.lexer.lineno += t.value.count('\n')
    raise ParseError("Unterminated string", t)

def t_assign_UNTERMINATEDSQUOTESTRING(t):
    r"'(\\'|\\\n|[^'\n])*?\n"
    t.lexer.lineno += t.value.count('\n')
    raise ParseError("Unterminated string", t)

def t_assign_UNQUOTEDSTRING(t):
    r".+"
    raise ParseError("Unquoted string", t)


def t_ANY_error(t):
    raise ParseError("Illegal character", t)


tokens = list(set(tokens))
