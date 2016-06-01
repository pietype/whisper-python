import ply.yacc as yacc

from lexer import WhisperLexer
from util import WRException


def pretty_print_syntax_errors(input):
    # adjusting for parse hack
    input = input[3:-1]

    def f(error):
        if error.lexpos > len(input):
            return 'Unexpected end of file'
        lines = input.split('\n')
        line_number = 0
        line_position = error.lexpos - 3
        while line_position >= len(lines[line_number]):
            line_position -= len(lines[line_number]) + 1  # +1 for newline
            line_number += 1

        line = lines[line_number]
        return 'Line {}\n{}\n{}^\n'.format(line_number + 1, line, line_position * ' ')

    return f


class WhisperParser(object):
    def __init__(self, **kwargs):
        self._calc_lexer = WhisperLexer()

        # build the parser
        self.tokens = self._calc_lexer.tokens
        self.lexer = self._calc_lexer._lexer
        self._parser = yacc.yacc(module=self, **kwargs)
        self._errors = []

    def parse(self, string):
        # hack - makes it easier to define start symbol for parsing files
        string = '(){' + string + '}'
        output = self._parser.parse(string)
        if output and not self._errors:
            return output
        exception = WRException("Syntax error\n" + ''.join(map(pretty_print_syntax_errors(string), self._errors)))
        self._errors = []
        raise exception

    @classmethod
    def _scope_values_to_dict(cls, dv):
        return dict([(l[1], l[2]) for l in dv[1][1]])

    # see parse
    def p_start(self, p):
        'start : newline_opt scope newline_opt'
        p[0] = p[2]

    def p_scope(self, p):
        'scope : LPAREN newline_opt RPAREN LBRACE newline_opt RBRACE'
        p[0] = ('create_scope', [], {}, None)

    def p_scope_expression(self, p):
        'scope : LPAREN newline_opt RPAREN LBRACE newline_opt infix_chain newline_opt RBRACE'
        p[0] = ('create_scope', [], {}, p[6])

    def p_scope_bind(self, p):
        'scope : LPAREN bind RPAREN LBRACE newline_opt RBRACE'
        p[0] = ('create_scope', p[2], {}, None)

    def p_scope_bind_expression(self, p):
        'scope : LPAREN bind RPAREN LBRACE newline_opt infix_chain newline_opt RBRACE'
        p[0] = ('create_scope', p[2], {}, p[6])

    def p_scope_bind_let_list(self, p):
        'scope : LPAREN bind RPAREN LBRACE newline_opt let_list newline_opt RBRACE'
        p[0] = ('create_scope', p[2], dict([(l[1], l[2]) for l in p[6]]), None)

    def p_scope_let_list(self, p):
        'scope : LPAREN newline_opt RPAREN LBRACE newline_opt let_list newline_opt RBRACE'
        p[0] = ('create_scope', [], dict([(l[1], l[2]) for l in p[6]]), None)

    # def p_scope_let_list(self, p):
    #     'scope : LBRACE newline_opt let_list newline_opt RBRACE'
    #     p[0] = ('create_scope', [], dict([(l[1], l[2]) for l in p[3]]), None)

    def p_scope_let_list_expression(self, p):
        'scope : LPAREN newline_opt RPAREN LBRACE newline_opt let_list separator infix_chain newline_opt RBRACE'
        p[0] = ('create_scope', [], dict([(l[1], l[2]) for l in p[6]]), p[8])

    def p_scope_bind_let_list_expression(self, p):
        'scope : LPAREN bind RPAREN LBRACE newline_opt let_list separator infix_chain newline_opt RBRACE'
        p[0] = ('create_scope', p[2], dict([(l[1], l[2]) for l in p[6]]), p[8])

    def p_bind(self, p):
        'bind : ident'
        p[0] = [(p[1], None)]

    def p_bind_default(self, p):
        'bind : ident COLON infix_chain'
        p[0] = [(p[1], p[3])]

    def p_bind_named(self, p):
        'bind : bind separator ident COLON infix_chain'
        p[0] = p[1] + [(p[3], p[5])]

    def p_let_list_let(self, p):
        'let_list : let'
        p[0] = [p[1]]

    def p_let_list_let_list(self, p):
        'let_list : let_list separator let'
        p[0] = p[1] + [p[3]]

    def p_let(self, p):
        'let : ident COLON infix_chain'
        p[0] = ('let', p[1], p[3])

    def p_import(self, p):
        'let : ident COLON IMPORT'
        p[0] = ('let', p[1], ('import', p[1]))

    def p_infix_chain_expression(self, p):
        'infix_chain : expression'
        p[0] = p[1]

    def p_infix_chain(self, p):
        'infix_chain : unresolved_infix_chain ident expression'
        p[0] = ('infix_chain', p[1] + [(p[2], p[3])])

    def p_infix_chain_newline(self, p):
        'infix_chain : unresolved_infix_chain ident newline expression'
        p[0] = ('infix_chain', p[1] + [(p[2], p[4])])

    def p_unresolved_infix_chain_expression(self, p):
        'unresolved_infix_chain : expression'
        p[0] = [(None, p[1])]

    def p_unresolved_infix_chain(self, p):
        'unresolved_infix_chain : unresolved_infix_chain ident expression'
        p[0] = p[1] + [(p[2], p[3])]

    def p_unresolved_infix_chain_newline(self, p):
        'unresolved_infix_chain : unresolved_infix_chain ident newline expression'
        p[0] = p[1] + [(p[2], p[4])]

    def p_expression_number(self, p):
        'expression : NUMBER'
        p[0] = ('create_number', p[1])

    def p_expression_dictionary(self, p):
        'expression : dictionary'
        p[0] = ('create_dictionary', p[1])

    def p_dictionary_empty(self, p):
        'dictionary : LBRACE newline_opt RBRACE'
        p[0] = []

    def p_dictionary(self, p):
        'dictionary : LBRACE newline_opt dictionary_items newline_opt RBRACE'
        p[0] = p[3]

    def p_dictionary_items_item(self, p):
        'dictionary_items : expression COLON expression'
        p[0] = [(p[1], p[3])]

    def p_dictionary_items_items(self, p):
        'dictionary_items : dictionary_items separator expression COLON expression'
        p[0] = p[1] + [(p[3], p[5])]

    def p_expression_list(self, p):
        'expression : list'
        p[0] = ('create_list', p[1])

    def p_list_empty(self, p):
        'list : LBRACKET newline_opt RBRACKET'
        p[0] = []

    def p_list(self, p):
        'list : LBRACKET newline_opt list_items newline_opt RBRACKET'
        p[0] = p[3]

    def p_list_items_item(self, p):
        'list_items : expression'
        p[0] = [p[1]]

    def p_list_items(self, p):
        'list_items : list_items separator expression'
        p[0] = p[1] + [p[3]]

    def p_ident_wrapper(self, p):
        'ident : IDENT'
        p[0] = ('create_string', p[1])

    def p_expression_ident(self, p):
        'expression : ident'
        p[0] = ('resolve', p[1], None)

    def p_expression_call(self, p):
        'expression : expression LPAREN newline_opt RPAREN'
        p[0] = ('call', p[1], [])

    def p_expression_call_arguments(self, p):
        'expression : expression LPAREN newline_opt arguments newline_opt RPAREN'
        p[0] = ('call', p[1], p[4])

    def p_arguments(self, p):
        'arguments : expression'
        p[0] = [(None, p[1])]

    def p_arguments_named(self, p):
        'arguments : arguments separator ident COLON expression'
        p[0] = p[1] + [(p[3], p[5])]

    def p_expression_chain(self, p):
        'expression : expression DOT ident'
        p[0] = ('resolve', p[3], p[1])

    def p_expression_chain_newline(self, p):
        'expression : expression DOT newline ident'
        p[0] = ('resolve', p[4], p[1])

    def p_expression_scope(self, p):
        'expression : scope'
        p[0] = p[1]

    def p_expression_string(self, p):
        'expression : STRING'
        p[0] = ('create_string', p[1])

    def p_expression_get(self, p):
        'expression : expression LBRACKET infix_chain RBRACKET'
        p[0] = ('get', p[1], p[3])

    def p_expression_slice(self, p):
        'expression : expression LBRACKET infix_chain COLON infix_chain RBRACKET'
        p[0] = ('slice', p[1], p[3], p[5])

    def p_expression_slice_from_beginning(self, p):
        'expression : expression LBRACKET COLON infix_chain RBRACKET'
        p[0] = ('slice', p[1], ('create_number', 0), p[4])

    def p_expression_slice_to_end(self, p):
        'expression : expression LBRACKET infix_chain COLON RBRACKET'
        p[0] = ('slice', p[1], p[3], None)

    def p_separator(self, p):
        '''separator : newline
                     | COMMA
                     | COMMA newline'''
        p[0] = None

    def p_newline_opt(self, p):
        '''newline_opt :
                       | newline'''
        p[0] = None

    def p_newline(self, p):
        'newline : NEWLINE'
        p[0] = None

    def p_newline_newline(self, p):
        'newline : NEWLINE newline'
        p[0] = None

    # TODO solve s/r conflict
    # def p_expression_parens(self, p):
    #     'expression : LPAREN expression RPAREN'
    #     p[0] = p[2]

    def p_error(self, p):
        # TODO
        if p:
            self._errors.append(p)
            pass # self._parser.errok()
        else:
            # hack handle eof, don't know why ply behaves this way
            from ply.lex import LexToken
            tok = LexToken()
            tok.value = self.lexer.lexdata[self.lexer.lexpos:]
            tok.lineno = self.lexer.lineno
            tok.type = 'error'
            tok.lexpos = self.lexer.lexpos
            self._parser.errok()
            return tok
