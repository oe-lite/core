import oelite.parse
import re

tokens = [
    'VARNAME', 'FLAG', 'OVERRIDE',
    'ASSIGN', 'EXPASSIGN', 'WEAKASSIGN', 'LAZYASSIGN',
    'APPEND', 'PREPEND', 'POSTDOT', 'PREDOT',
    'STRING', 'QUOTE',
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
    'prefer'	: 'PREFER',
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
    ('prefer', 'exclusive'),
    ('preferpackage', 'exclusive'),
    ('packages', 'exclusive'),
    ('preferrecipe', 'exclusive'),
    ('preferlayer', 'exclusive'),
    ('preferversion', 'exclusive'),
    ('dquote', 'exclusive'),
    ('squote', 'exclusive'),
    ('tripledquote', 'exclusive'),
    ('triplesquote', 'exclusive'),
    )

precedence = ()

literals = ''


t_ignore = ' \t'

def t_VARNAME(t):
    #r'[a-zA-Z][a-zA-Z0-9_\-\${}\+\.]*'
    r'[a-zA-Z_][a-zA-Z0-9_\-\${}\+\.]*'
    #r'[a-zA-Z_][a-zA-Z0-9_\-\${}/\+\.]*'
    t.type = reserved.get(t.value, 'VARNAME')
    if t.type == 'VARNAME':
        pass
    elif t.type in ('INCLUDE', 'INHERIT', 'ADDTASK', 'ADDHOOK', 'DEF',
                    'PREFER'):
        t.lexer.push_state(t.value)
    elif t.type == 'REQUIRE':
        t.lexer.push_state('include')
    #print "VARNAME %s %s"%(t.type, t.value)
    return t

def t_OVERRIDE(t):
    r':[a-zA-Z0-9\-_]+'
    t.value = ('', t.value[1:])
    return t

def t_OVERRIDE2(t):
    r':[\>\<][a-zA-Z0-9\-_]+'
    t.type = 'OVERRIDE'
    t.value = (t.value[1], t.value[2:])
    return t

def t_FLAG(t):
    r'\[[a-zA-Z_][a-zA-Z0-9_]*\]'
    #t.type = reserved.get(t.value, 'FLAG')
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
    'post_common_inherits',
    'pre_recipe_parse',
    'mid_recipe_parse',
    'post_recipe_parse',
    'post_extra_arch',
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


t_prefer_ignore = ' \t'

tokens += [ 'PACKAGE', 'RECIPE', 'LAYER', 'VERSION',
            'PACKAGENAME', 'RECIPENAME', 'LAYERNAME', 'VERSIONNAME' ]

def t_prefer_PACKAGE(t):
    r'package'
    t.lexer.push_state('preferpackage')
    return t

def t_prefer_RECIPE(t):
    r'recipe'
    t.lexer.push_state('preferrecipe')
    return t

def t_prefer_LAYER(t):
    r'layer'
    t.lexer.push_state('preferlayer')
    return t

def t_prefer_VERSION(t):
    r'version'
    t.lexer.push_state('preferversion')
    return t

t_preferpackage_ignore = ' \t'

def t_preferpackage_PACKAGENAME(t):
    r'[a-z][a-z0-9\-\+]*'
    t.lexer.push_state('packages')
    return t

t_packages_ignore = ','

def t_packages_PACKAGENAME(t):
    r'[a-z][a-z0-9\-\+]*'
    return t

def t_packages_WHITESPACE(t):
    r'[ \t]'
    t.lexer.pop_state()
    t.lexer.pop_state()
    return

def t_packages_NEWLINE(t):
    r'\n'
    t.lexer.lineno += 1
    t.lexer.pop_state()
    t.lexer.pop_state()
    t.lexer.pop_state()
    return t

t_preferrecipe_ignore = ' \t'

def t_preferrecipe_RECIPENAME(t):
    r'[a-z][a-z0-9\-\+_/\.]*'
    t.lexer.pop_state()
    return t

t_preferlayer_ignore = ' \t'

def t_preferlayer_LAYERNAME(t):
    r'[a-z][a-z0-9\-\+_/\.]*'
    t.lexer.pop_state()
    return t

t_preferversion_ignore = ' \t'

def t_preferversion_VERSIONNAME(t):
    r'[0-9\.a-z\-]+'
    t.lexer.pop_state()
    return t

def t_prefer_NEWLINE(t):
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

def t_assign_TRIPLEDQUOTE(t):
    r'"""'
    t.type = "QUOTE"
    t.lexer.push_state('tripledquote')
    return t

def t_assign_TRIPLESQUOTE(t):
    r"'''"
    t.type = "QUOTE"
    t.lexer.push_state('triplesquote')
    return t

def t_assign_DQUOTE(t):
    r'"'
    t.type = "QUOTE"
    t.lexer.push_state('dquote')
    return t

def t_assign_SQUOTE(t):
    r"'"
    t.type = "QUOTE"
    t.lexer.push_state('squote')
    return t

t_dquote_ignore = ''

def t_dquote_STRING(t):
    r'(\\"|\\\n|[^"\n])+'
    t.type = "STRING"
    t.lexer.lineno += t.value.count('\n')
    t.value = re.sub(r"(\s+\\\n(\s+)?)|(\\\n\s+)", " ", t.value)
    t.value = t.value.decode("string-escape")
    return t

def t_dquote_QUOTE(t):
    r'"'
    t.type = "QUOTE"
    t.lexer.pop_state()
    t.lexer.pop_state()
    return t

def t_dquote_UNTERMINATEDSTRING(t):
    r'\n'
    t.lexer.lineno += t.value.count('\n')
    # ParseError-5
    raise oelite.parse.ParseError(t.lexer.parser, "Unterminated string", t)

t_squote_ignore = ''

def t_squote_STRING(t):
    r"(\\'|\\\n|[^'\n])+"
    t.type = "STRING"
    t.lexer.lineno += t.value.count('\n')
    t.value = re.sub(r"(\s+\\\n(\s+)?)|(\\\n\s+)", " ", t.value)
    t.value = t.value.decode("string-escape")
    return t

def t_squote_QUOTE(t):
    r"'"
    t.type = "QUOTE"
    t.lexer.pop_state()
    t.lexer.pop_state()
    return t

def t_squote_UNTERMINATEDSTRING(t):
    r"\n"
    t.lexer.lineno += t.value.count('\n')
    # ParseError-6
    raise oelite.parse.ParseError(t.lexer.parser, "Unterminated string", t)

t_tripledquote_ignore = ''

def t_tripledquote_STRING(t):
    r'([^"\\\n]|\\[0-7]{1,3}|\\x[0-9a-fA-F]{2}|\\[^0-7x\n])+'
    t.type = "STRING"
    t.value = t.value.decode("string-escape")
    return t

def t_tripledquote_ESCEOL(t):
    r'\\\n'
    t.type = "STRING"
    t.value = ""
    t.lexer.lineno += 1
    return t

def t_tripledquote_EOL(t):
    r'\n'
    t.type = "STRING"
    t.lexer.lineno += 1
    return t

def t_tripledquote_QUOTE(t):
    r'"{3}'
    t.type = "QUOTE"
    t.lexer.pop_state()
    t.lexer.pop_state()
    return t

def t_tripledquote_INQUOTE(t):
    r'"{1,2}'
    t.type = "STRING"
    return t

t_triplesquote_ignore = ''

def t_triplesquote_STRING(t):
    r"([^'\\\n]|\\[0-7]{1,3}|\\x[0-9a-fA-F]{2}|\\[^0-7x\n])+"
    t.type = "STRING"
    t.value = t.value.decode("string-escape")
    return t

def t_triplesquote_ESCEOL(t):
    r'\\\n'
    t.type = "STRING"
    t.value = ""
    t.lexer.lineno += 1
    return t

def t_triplesquote_EOL(t):
    r'\n'
    t.type = "STRING"
    t.lexer.lineno += 1
    return t

def t_triplesquote_QUOTE(t):
    r'"{3}'
    t.type = "QUOTE"
    t.lexer.pop_state()
    t.lexer.pop_state()
    return t

def t_triplesquote_INQUOTE(t):
    r'"{1,2}'
    t.type = "STRING"
    return t

# ParseError-7
def t_assign_UNQUOTEDSTRING(t):
    r".+"
    raise oelite.parse.ParseError(t.lexer.parser, "Unquoted string", t)


def t_ANY_error(t):
    # ParseError-8
    raise oelite.parse.ParseError(t.lexer.parser, "Illegal character", t)


tokens = list(set(tokens))
