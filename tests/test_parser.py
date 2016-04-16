from unittest import TestCase

from parser import DELParser
from runtime import evaluate, D, S, N


EXPRESSIONS = [
    'a: 1\n1\n',
    'a: 2\na\n',
    'a: { 1 }\na()\n',
    'f: (a){ a }\nf(3)\n',
    'd: { f: { 1 }\n1 }\nd.f()\n',

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
    [
        ('IDENT', 'a'),
        ('COLON', ':'),
        ('NUMBER', 1),
        ('NEWLINE', '\n'),
        ('NUMBER', 1),
        ('NEWLINE', '\n'),
    ],
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

PARSER_EXPECTED = [
    ('create_dict', [], {('create_string', 'a'): ('create_number', 1)}, ('create_number', 1)),
    ('create_dict', [], {('create_string', 'a'): ('create_number', 2)}, ('resolve', ('create_string', 'a'), None)),
    ('create_dict', [], {('create_string', 'a'): ('create_dict', [], {}, ('create_number', 1))}, ('call', ('resolve', ('create_string', 'a'), None), [])),
]

PARSER_ERROR_EXPECTED = [
    'Syntax error\nLine 1\na 1\n  ^\n',
    'Syntax error\nLine 1\na 1\n ^\nLine 2\nf: { 1\n      ^\n',
]

RUNTIME_EXPECTED = [
    N(1),
    N(2),
    N(1),
    N(3),
    N(1),
    N(1),
    N(2),
    N(1),
]


def _generate_test_case(expression, expected_output):
    def test_case(self):
        self._test(expression, expected_output)
    return test_case


class TestLexer(TestCase):
    def _test(self, string, expected_output):
        from lexer import DELLexer
        l = DELLexer()
        output = [(t.type, t.value) for t in l.tokenize(string)]
        self.assertEquals(output, expected_output)

for e, o, i in zip(EXPRESSIONS, LEXER_EXPECTED, range(min(len(EXPRESSIONS), len(LEXER_EXPECTED)))):
    name = 'test_E{}'.format(i)
    setattr(TestLexer, name, _generate_test_case(e, o))


class TestParser(TestCase):
    def _test(self, string, expected_output):
        p = DELParser(method='LALR')
        output = p.parse(string)
        self.assertEquals(output, expected_output)

for e, o, i in zip(EXPRESSIONS, PARSER_EXPECTED, range(min(len(EXPRESSIONS), len(PARSER_EXPECTED)))):
    name = 'test_E{}'.format(i)
    setattr(TestParser, name, _generate_test_case(e, o))


class TestParserErrors(TestCase):
    def _test(self, string, expected_errors):
        try:
            p = DELParser(method='LALR')
            output = p.parse(string)
            assert False
        except Exception as e:
            self.assertEquals(e.message, expected_errors)


for e, o, i in zip(ERROR_EXPRESSIONS, PARSER_ERROR_EXPECTED, range(min(len(ERROR_EXPRESSIONS), len(PARSER_ERROR_EXPECTED)))):
    name = 'test_E{}'.format(i)
    setattr(TestParserErrors, name, _generate_test_case(e, o))


class TestRuntime(TestCase):
    def _test(self, string, expected_output):
        p = DELParser(method='LALR')
        node = p.parse(string)
        output = evaluate(('call', node, []))
        self.assertEquals(output._raw, expected_output._raw)

    def test_new(self):
        expression = '''f: (a){
  a + 1
}

{
  g: (a){
    f(a) + 1
  }
  g(1)
}()
'''
        expected_output = N(3)
        self._test(expression, expected_output)

    def test_new2(self):
        expression = '''1 + 1
'''
        expected_output = N(2)
        self._test(expression, expected_output)

    def test_new3(self):
        expression = '"abc".length()'
        expected_output = N(3)
        self._test(expression, expected_output)

    def test_new4(self):
        expression = '1 = 1'
        expected_output = True
        self._test(expression, expected_output)

    def test_new5(self):
        expression = '"abc"[1:]'
        expected_output = S("bc")
        self._test(expression, expected_output)

    def test_new7(self):
        expression = '''f: (a){
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
        expected_output = N(6)
        self._test(expression, expected_output)

    def test_new6(self):
        expression = '''
Automaton: (states){           # handle two argument match
  match: (input){              # external interface
    match: (input, state: 0){  # implementation with internal binding
      next: states[state][input[0]]
      match(input[1:], state: next) or state = states.length()
    }

    match(input)
  }
}
input: "ab"

Automaton([{
  a: 1
},
{
  b: 2
}]).match(input)'''
        expected_output = True
        self._test(expression, expected_output)



    # def test_old(self):
    #     expression = '"a".length() = 1\n'
    #     expected_output = N(1)
    #     self._test(expression, expected_output)


for e, o, i in zip(EXPRESSIONS, RUNTIME_EXPECTED, range(min(len(EXPRESSIONS), len(RUNTIME_EXPECTED)))):
    name = 'test_E{}'.format(i)
    setattr(TestRuntime, name, _generate_test_case(e, o))
