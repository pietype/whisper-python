from unittest import TestCase, skip

from src.parser import WhisperParser


class TestParser(TestCase):
    def _test(self, string, expected_output):
        p = WhisperParser()
        output = p.parse(string)
        self.assertEquals(output, expected_output)

    def test_scope1(self):
        expression = 'a: 1\n1'
        expected_output = ('create_scope', [], {('create_string', 'a'): ('create_number', 1)}, ('create_number', 1))
        self._test(expression, expected_output)

    def test_scope2(self):
        expression = 'a: 2\na'
        expected_output = ('create_scope', [], {('create_string', 'a'): ('create_number', 2)}, ('resolve', ('create_string', 'a'), None))
        self._test(expression, expected_output)

    def test_function_scope(self):
        expression = 'a: (){ 1 }\na()'
        expected_output = ('create_scope', [], {('create_string', 'a'): ('create_scope', [], {}, ('create_number', 1))}, ('call', ('resolve', ('create_string', 'a'), None), []))
        self._test(expression, expected_output)
        
    def test_function_argument(self):
        expression = 'f: (a){ a }\nf(3)'
        expected_output = ('create_scope',
                           [],
                           {('create_string', 'f'): ('create_scope',
                                                     [(('create_string', 'a'), None)],
                                                     {},
                                                     ('resolve', ('create_string', 'a'), None))},
                           ('call',
                            ('resolve', ('create_string', 'f'), None),
                            [(None, ('create_number', 3))]))
        self._test(expression, expected_output)
        
    def test_method(self):
        expression = 'd: (){ f: (){ 1 } }\nd.f()'
        expected_output = ('create_scope',
                           [],
                           {('create_string', 'd'): ('create_scope',
                                                     [],
                                                     {('create_string', 'f'): ('create_scope',
                                                                               [],
                                                                               {},
                                                                               ('create_number', 1))},
                                                     None)},
                           ('call',
                            ('resolve',
                             ('create_string', 'f'),
                             ('resolve',
                              ('create_string', 'd'), None)),
                            []))
        self._test(expression, expected_output)
        
    def test_object_as_dictionary_access1(self):
        expression = '(){a: 1}["a"]'
        expected_output = ('create_scope',
                           [],
                           {},
                           ('get',
                            ('create_scope',
                             [],
                             {('create_string', 'a'): ('create_number', 1)},
                             None),
                            ('create_string', 'a')))
        self._test(expression, expected_output)
        
    def test_object_as_dictionary_access2(self):
        expression = '(){a: 1\nb: 2}["b"]'
        expected_output = ('create_scope',
                           [],
                           {},
                           ('get',
                            ('create_scope',
                             [],
                             {('create_string', 'a'): ('create_number', 1),
                              ('create_string', 'b'): ('create_number', 2)},
                             None),
                            ('create_string', 'b')))
        self._test(expression, expected_output)
        
    
class TestParserErrors(TestCase):
    def _test(self, string, expected_errors):
        try:
            p = WhisperParser(method='LALR')
            output = p.parse(string)
            assert False
        except Exception as e:
            self.assertEquals(e.message, expected_errors)

    @skip
    def test_missing_colon(self):
        e = 'a 1'
        self._test(e, 'Syntax error\nLine 1\na 1\n  ^')

    @skip
    def test_e1(self):
        e = 'a 1\nf: { 1'
        self._test(e, 'Syntax error\nLine 1\na 1\n ^\nLine 2\nf: { 1\n      ^')
