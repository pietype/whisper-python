from unittest import TestCase


class TestLexer(TestCase):
    def _test(self, string, expected_output):
        from src.lexer import WhisperLexer
        l = WhisperLexer()
        output = [(t.type, t.value) for t in l.tokenize(string)]
        self.assertEqual(output, expected_output)

    def test_scope1(self):
        expression = 'a: 1\n1\n'
        expected_result = [
            ('IDENT', 'a'),
            ('COLON', ':'),
            ('NUMBER', 1),
            ('NEWLINE', '\n'),
            ('NUMBER', 1),
            ('NEWLINE', '\n'),
        ]
        self._test(expression, expected_result)

    def test_scope2(self):
        expression = 'a: 2\na\n'
        expected_result = [
            ('IDENT', 'a'),
            ('COLON', ':'),
            ('NUMBER', 2),
            ('NEWLINE', '\n'),
            ('IDENT', 'a'),
            ('NEWLINE', '\n'),
        ]
        self._test(expression, expected_result)

    def test_function(self):
        expression = 'a: (){ 1 }\na()\n'
        expected_result = [
            ('IDENT', 'a'),
            ('COLON', ':'),
            ('LPAREN', '('),
            ('RPAREN', ')'),
            ('LBRACE', '{'),
            ('NUMBER', 1),
            ('RBRACE', '}'),
            ('NEWLINE', '\n'),
            ('IDENT', 'a'),
            ('LPAREN', '('),
            ('RPAREN', ')'),
            ('NEWLINE', '\n'),
        ]
        self._test(expression, expected_result)

    def test_function_argument(self):
        expression = 'f: (a){ a }\nf(3)\n'
        expected_result = [
            ('IDENT', 'f'),
            ('COLON', ':'),
            ('LPAREN', '('),
            ('IDENT', 'a'),
            ('RPAREN', ')'),
            ('LBRACE', '{'),
            ('IDENT', 'a'),
            ('RBRACE', '}'),
            ('NEWLINE', '\n'),
            ('IDENT', 'f'),
            ('LPAREN', '('),
            ('NUMBER', 3),
            ('RPAREN', ')'),
            ('NEWLINE', '\n'),
        ]
        self._test(expression, expected_result)

    def test_method(self):
        expression = 'd: (){ f: (){ 1 } }\nd.f()\n'
        expected_result = [
            ('IDENT', 'd'),
            ('COLON', ':'),
            ('LPAREN', '('),
            ('RPAREN', ')'),
            ('LBRACE', '{'),
            ('IDENT', 'f'),
            ('COLON', ':'),
            ('LPAREN', '('),
            ('RPAREN', ')'),
            ('LBRACE', '{'),
            ('NUMBER', 1),
            ('RBRACE', '}'),
            ('RBRACE', '}'),
            ('NEWLINE', '\n'),
            ('IDENT', 'd'),
            ('DOT', '.'),
            ('IDENT', 'f'),
            ('LPAREN', '('),
            ('RPAREN', ')'),
            ('NEWLINE', '\n'),
        ]
        self._test(expression, expected_result)

    def test_object_as_dictionary_access1(self):
        expression = '(){a: 1}["a"]\n'
        expected_result = [
            ('LPAREN', '('),
            ('RPAREN', ')'),
            ('LBRACE', '{'),
            ('IDENT', 'a'),
            ('COLON', ':'),
            ('NUMBER', 1),
            ('RBRACE', '}'),
            ('LBRACKET', '['),
            ('STRING', 'a'),
            ('RBRACKET', ']'),
            ('NEWLINE', '\n'),
        ]
        self._test(expression, expected_result)

    def test_object_as_dictionary_access2(self):
        expression = '(){a: 1\nb: 2}["b"]\n'
        expected_result = [
            ('LPAREN', '('),
            ('RPAREN', ')'),
            ('LBRACE', '{'),
            ('IDENT', 'a'),
            ('COLON', ':'),
            ('NUMBER', 1),
            ('NEWLINE', '\n'),
            ('IDENT', 'b'),
            ('COLON', ':'),
            ('NUMBER', 2),
            ('RBRACE', '}'),
            ('LBRACKET', '['),
            ('STRING', 'b'),
            ('RBRACKET', ']'),
            ('NEWLINE', '\n'),
        ]
        self._test(expression, expected_result)

    def test_error_expression1(self):
        expression = 'a 1\n'
        expected_result = [
            ('IDENT', 'a'),
            ('NUMBER', 1),
            ('NEWLINE', '\n'),
        ]
        self._test(expression, expected_result)

    # example of a not so useful lexer test - this is an error only on parser level
    def test_error_expression2(self):
        expression = 'a 1\nf: { 1\n'
        expected_result = [
            ('IDENT', 'a'),
            ('NUMBER', 1),
            ('NEWLINE', '\n'),
            ('IDENT', 'f'),
            ('COLON', ':'),
            ('LBRACE', '{'),
            ('NUMBER', 1),
            ('NEWLINE', '\n'),
        ]
        self._test(expression, expected_result)

    # example of a decent lexer logic test
    def test_empty_string1(self):
        expression = '""'
        expected_output = [
            ('STRING', '')
        ]
        self._test(expression, expected_output)

    def test_empty_string2(self):
        expression = "''"
        expected_output = [
            ('STRING', '')
        ]
        self._test(expression, expected_output)
