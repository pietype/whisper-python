from unittest import TestCase, skip

from parser import WhisperParser
from runtime import evaluate


EXPRESSIONS = [
    '',
    '',
    '',  # 'a: (){ 1 }\na()\n',
    '',  # 'f: (a){ a }\nf(3)\n',
    '',  # 'd: { f: { 1 }\n1 }\nd.f()\n',

    '{a: 1}["a"]\n',
    '{a: 1\nb: 2}["b"]\n',

    'hello: import\nhello.a\n',
    '''re: import
{
  a1: re.Automaton([
    re.State({a: 1})
    re.State({b: 2})
  ])
  input: "ab"

  a1.match(input)
}()
''',
]

ERROR_EXPRESSIONS = [
    'a 1\n',
    'a 1\nf: { 1\n',
]

LEXER_EXPECTED = [
    [],
    [
        ('IDENT', 'a'),
        ('COLON', ':'),
        ('NUMBER', 2),
        ('NEWLINE', '\n'),
        ('IDENT', 'a'),
        ('NEWLINE', '\n'),
    ],
    [
        ('IDENT', 'a'),
        ('COLON', ':'),
        ('LBRACE', '{'),
        ('NUMBER', 1),
        ('RBRACE', '}'),
        ('NEWLINE', '\n'),
        ('IDENT', 'a'),
        ('LPAREN', '('),
        ('RPAREN', ')'),
        ('NEWLINE', '\n'),
    ],
    [],  # TODO
    [
        ('IDENT', 'd'),
        ('COLON', ':'),
        ('LBRACE', '{'),
        ('IDENT', 'f'),
        ('COLON', ':'),
        ('LBRACE', '{'),
        ('NUMBER', 1),
        ('RBRACE', '}'),
        ('NEWLINE', '\n'),
        ('NUMBER', 1),
        ('RBRACE', '}'),
        ('NEWLINE', '\n'),
        ('IDENT', 'd'),
        ('DOT', '.'),
        ('IDENT', 'f'),
        ('LPAREN', '('),
        ('RPAREN', ')'),
        ('NEWLINE', '\n'),
    ],
    [
        ('LBRACE', '{'),
        ('IDENT', 'a'),
        ('COLON', ':'),
        ('NUMBER', 1),
        ('RBRACE', '}'),
        ('LBRACKET', '['),
        ('STRING', 'a'),
        ('RBRACKET', ']'),
        ('NEWLINE', '\n'),
    ],
    [],  # TODO
    [
        ('IDENT', 'hello'),
        ('COLON', ':'),
        ('IMPORT', 'import'),
        ('NEWLINE', '\n'),
        ('IDENT', 'hello'),
        ('DOT', '.'),
        ('IDENT', 'a'),
        ('NEWLINE', '\n'),
    ],
]

PARSER_ERROR_EXPECTED = [
    'Syntax error\nLine 1\na 1\n  ^\n',
    'Syntax error\nLine 1\na 1\n ^\nLine 2\nf: { 1\n      ^\n',
]

RUNTIME_EXPECTED = [
    1,
    2,
    1,
    3,
    1,
    1,
    2,
    1,
]


def _generate_test_case(expression, expected_output):
    def test_case(self):
        self._test(expression, expected_output)
    return test_case


# class TestLexer(TestCase):
#     def _test(self, string, expected_output):
#         from lexer import WhisperLexer
#         l = WhisperLexer()
#         output = [(t.type, t.value) for t in l.tokenize(string)]
#         self.assertEquals(output, expected_output)
#
#     def test_current_scope(self):
#         expression = 'a: 1\n1\n'
#         expected_result = [
#             ('IDENT', 'a'),
#             ('COLON', ':'),
#             ('NUMBER', 1),
#             ('NEWLINE', '\n'),
#             ('NUMBER', 1),
#             ('NEWLINE', '\n'),
#         ]
#         self._test(expression, expected_result)
#
#     def test_e1(self):
#         self._test(EXPRESSIONS[1], LEXER_EXPECTED[1])
#
#     def test_e2(self):
#         self._test(EXPRESSIONS[2], LEXER_EXPECTED[2])
#
#     @skip
#     def test_e3(self):
#         self._test(EXPRESSIONS[3], LEXER_EXPECTED[3])
#
#     def test_e4(self):
#         self._test(EXPRESSIONS[4], LEXER_EXPECTED[4])
#
#     def test_e5(self):
#         self._test(EXPRESSIONS[5], LEXER_EXPECTED[5])
#
#     @skip
#     def test_e6(self):
#         self._test(EXPRESSIONS[6], LEXER_EXPECTED[6])
#
#     def test_e7(self):
#         self._test(EXPRESSIONS[7], LEXER_EXPECTED[7])
#
#     # def test_e8(self):
#     #     self._test(EXPRESSIONS[8], LEXER_EXPECTED[8])
#
#     def test_empty_string1(self):
#         expression = '""'
#         expected_output = [
#             ('STRING', '')
#         ]
#         self._test(expression, expected_output)
#
#     def test_empty_string2(self):
#         expression = "''"
#         expected_output = [
#             ('STRING', '')
#         ]
#         self._test(expression, expected_output)


class TestParser(TestCase):
    def _test(self, string, expected_output):
        p = WhisperParser(method='LALR')
        output = p.parse(string)
        self.assertEquals(output, expected_output)

    def test_current_scope1(self):
        expression = 'a: 1\n1\n'
        expected_output = ('create_scope', [], {('create_string', 'a'): ('create_number', 1)}, ('create_number', 1))
        self._test(expression, expected_output)

    def test_current_scope2(self):
        expression = 'a: 2\na\n'
        expected_output = ('create_scope', [], {('create_string', 'a'): ('create_number', 2)}, ('resolve', ('create_string', 'a'), None))
        self._test(expression, expected_output)

    def test_function_scope(self):
        expression = 'a: (){ 1 }\na()\n'
        expected_output = ('create_scope', [], {('create_string', 'a'): ('create_scope', [], {}, ('create_number', 1))}, ('call', ('resolve', ('create_string', 'a'), None), []))
        self._test(expression, expected_output)


class TestParserErrors(TestCase):
    def _test(self, string, expected_errors):
        try:
            p = WhisperParser(method='LALR')
            output = p.parse(string)
            assert False
        except Exception as e:
            self.assertEquals(e.message, expected_errors)

    def test_e0(self):
        self._test(ERROR_EXPRESSIONS[0], PARSER_ERROR_EXPECTED[0])

    @skip  # TODO
    def test_e1(self):
        self._test(ERROR_EXPRESSIONS[1], PARSER_ERROR_EXPECTED[1])


class TestRuntime(TestCase):
    def _test(self, string, expected_output):
        p = WhisperParser(method='LALR')
        node = p.parse(string)
        output = evaluate(('call', node, []))
        self.assertEquals(output.raw, expected_output)

    # def test_e0(self):
    #     self._test(EXPRESSIONS[0], RUNTIME_EXPECTED[0])

    # def test_e1(self):
    #     self._test(EXPRESSIONS[1], RUNTIME_EXPECTED[1])
    #
    # def test_e2(self):
    #     self._test(EXPRESSIONS[2], RUNTIME_EXPECTED[2])
    #
    # def test_e3(self):
    #     self._test(EXPRESSIONS[3], RUNTIME_EXPECTED[3])
    #
    # def test_e4(self):
    #     self._test(EXPRESSIONS[4], RUNTIME_EXPECTED[4])
    #
    # def test_e5(self):
    #     self._test(EXPRESSIONS[5], RUNTIME_EXPECTED[5])
    #
    # def test_e6(self):
    #     self._test(EXPRESSIONS[6], RUNTIME_EXPECTED[6])
    #
    # def test_e7(self):
    #     self._test(EXPRESSIONS[7], RUNTIME_EXPECTED[7])

    # def test_e8(self):
    #     self._test(EXPRESSIONS[8], RUNTIME_EXPECTED[8])

    def test_new(self):
        expression = '''f: (a){
  a + 1
}

(){
  g: (a){
    f(a) + 1
  }
  g(1)
}()
'''
        expected_output = 3
        self._test(expression, expected_output)

    def test_new2(self):
        expression = '''1 + 1
'''
        expected_output = 2
        self._test(expression, expected_output)

    def test_new3(self):
        expression = '"abc".length()'
        expected_output = 3
        self._test(expression, expected_output)

    @skip  # equality operator, boolean type not implemented
    def test_new4(self):
        expression = '1 = 1'
        expected_output = True
        self._test(expression, expected_output)

    def test_new5(self):
        expression = '"abc"[1:]'
        expected_output = "bc"
        self._test(expression, expected_output)

    def test_new7(self):
        expression = '''
        f: (a){
          g: (b){
            h: (b){
              c: a + b
              a + c
            }
            h(b)
          }
          g(a)
        }

        f(2)
        '''
        expected_output = 6
        self._test(expression, expected_output)

    def test_problem(self):
        expression = '''
        f: (a){
          g: (b){
            c: b
            c
          }
          g(a)
        }
        f(1)
        '''
        self._test(expression, 1)

    def test_problem2(self):
        expression = '''
        f: (a){
          b: a
          b
        }
        f(1)
        '''
        self._test(expression, 1)

    def test_constructor(self):
        expression = '''
        O: (v){
          m: (){ v }
        }
        O(1).m()'''
        expected_output = 1
        self._test(expression, expected_output)

    def test_item_resolution1(self):
        expression = '''
        m: 1
        (){
          m: m
          m
        }()'''
        expected_output = 1
        self._test(expression, expected_output)

    def test_item_resolution2(self):
        expression = '''
        m: 1
        (){
          m: m
        }.m'''
        expected_output = 1
        self._test(expression, expected_output)
