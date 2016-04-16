import ply.lex as lex


class DELLexer(object):
    def __init__(self, **kwargs):
        self._lexer = lex.lex(module=self, **kwargs)

    def tokenize(self, string):
        self._lexer.input(string)
        t = self._lexer.token()
        while t:
            yield t
            t = self._lexer.token()

    reserved = {
        'import': 'IMPORT',
    }

    tokens = [
        'COLON',
        'DOT',
        'COMMA',
        'LBRACE',
        'RBRACE',
        'LPAREN',
        'RPAREN',
        'LBRACKET',
        'RBRACKET',

        'NEWLINE',

        'STRING',
        'NUMBER',
        'IDENT',
    ] + reserved.values()

    def t_COLON(self, t):
        r'\:'
        return t

    def t_DOT(self, t):
        r'\.'
        return t

    def t_COMMA(self, t):
        r'\,'
        return t

    def t_LBRACE(self, t):
        r'\{'
        return t

    def t_RBRACE(self, t):
        r'\}'
        return t

    def t_LPAREN(self, t):
        r'\('
        return t

    def t_RPAREN(self, t):
        r'\)'
        return t

    def t_LBRACKET(self, t):
        r'\['
        return t

    def t_RBRACKET(self, t):
        r'\]'
        return t

    def t_NEWLINE(self, t):  # includes single line comments
        r'(\s*\#.*)?\n'
        t.lexer.lineno += 1
        return t

    # TODO this pattern is basically useless - no escapes etc
    def t_STRING(self, t):
        r'(".+?")|(\'.+?\')'
        t.value = t.value[1:-1]
        return t

    def t_NUMBER(self, t):
        r'\d+'
        t.value = int(t.value)
        return t

    def t_ignore_WHITESPACE(self, t):
        r'\s+'

    def t_IDENT(self, t):
        r'.[^:\.,\[\]{}()\n\s]*'
        if t.value in self.reserved:
            t.type = self.reserved[t.value]

        return t

    def t_error(self, t):
        raise Exception("Illegal character {}".format(t))
