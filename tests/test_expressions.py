from unittest import TestCase, skip

from parser import WhisperParser
from runtime import evaluate
from util import WRException


class TestBase(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.parser = WhisperParser(method='LALR')

    def _test(self, expression, expected_result):
        node = self.parser.parse(expression)
        output = evaluate(('call', node, []))
        if type(expected_result) is list:
            for r, e in zip(output.raw, expected_result):
                self.assertEquals(r.raw, e)
        else:
            self.assertEquals(output.raw, expected_result)

    def _test_failed(self, expression):
        node = self.parser.parse(expression)
        output = evaluate(('call', node, []))
        self.assertTrue(type(output.raw) is WRException)


class TestFunction(TestBase):
    def test_expression1(self):
        e = '''
        1'''
        self._test(e, 1)

    def test_let1(self):
        e = '''
        a: 2
        a'''
        self._test(e, 2)

    def test_define1(self):
        e = '''
        f: (){ 3 }
        f()'''
        self._test(e, 3)

    def test_define_argument1(self):
        e = '''
        f: (a){ a }
        f(4)'''
        self._test(e, 4)

    def test_define_object_static1(self):
        e = '''
        o: (){
          m: (){ 5 }
        }
        o.m()'''
        self._test(e, 5)


class TestList(TestBase):
    def test_length1(self):
        e = '''
        [].length()'''
        self._test(e, 0)

    def test_length2(self):
        e = '''
        [0].length()'''
        self._test(e, 1)

    def test_length3(self):
        e = '''
        [0, 1, 2, 3, 4].length()'''
        self._test(e, 5)

    def test_slice1(self):
        e = '''
        [0, 1, 2, 3][1:2]'''
        self._test(e, [1, 2])

    def test_slice2(self):
        e = '''
        [0, 1, 2, 3][2:]'''
        self._test(e, [2, 3])

    def test_slice3(self):
        e = '''
        [0, 1, 2, 3][:2]'''
        self._test(e, [0, 1])

    def test_slice4(self):
        e = '''
        [0, 1, 2, 3][3:5]'''
        self._test(e, [3])

    def test_slice5(self):
        e = '''
        [0, 1, 2, 3][6:7]'''
        self._test(e, [])

    def test_map1(self):
        e = '''
        [].map((e){ e })'''
        self._test(e, [])

    def test_map2(self):
        e = '''
        [0, 1].map((e){ e })'''
        self._test(e, [0, 1])

    def test_map3(self):
        e = '''
        [0, 1, 2, 3].map((e){ e + 1 })'''
        self._test(e, [1, 2, 3, 4])

    def test_reduce_sum1(self):
        e = '''
        [0, 1].reduce((a){ (b){ a + b } })'''
        self._test(e, 1)

    def test_reduce_sum2(self):
        e = '''
        [0, 1, 2, 3, 4, 5].reduce((a){ (b){ a + b } })'''
        self._test(e, 15)

    def test_reduce_sum_single(self):
        e = '''
        [1].reduce((a){ (b){ a + b } })'''
        self._test(e, 1)

    def test_reduce_sum_empty(self):
        e = '''
        [].reduce((a){ (b){ a + b } })'''
        self._test_failed(e)

    def test_map_reduce(self):
        e = '''
        [0, 1, 2].map((e){ e + 1 }).reduce((a){ (b){ a + b } })'''
        self._test(e, 6)


class TestString(TestBase):
    def test_slice1(self):
        e = '''
        'abc'[1:]'''
        self._test(e, 'bc')

    def test_get1(self):
        e = '''
        'abc'[1:2]'''
        self._test(e, 'b')

    def test_add1(self):
        e = """
        'a' + 'b'"""
        self._test(e, 'ab')

    def test_add2(self):
        e = """
        '' + 'b'"""
        self._test(e, 'b')

    def test_add3(self):
        e = """
        'a' + ''"""
        self._test(e, 'a')


class TestDictionary(TestBase):
    def test_create1(self):
        e = '''
        {}'''
        self._test(e, {})

    def test_get1(self):
        e = '''
        {'a': 1}['a']'''
        self._test(e, 1)


class Experimental(TestBase):
    def test_import_re1(self):
        expression = '''
        RegularExpressions: import
        RegularExpressions.Node({'a': 1}).match('a')'''
        expected_output = True  # TODO apparently 1 == True, not sure this works fine
        self._test(expression, expected_output)

    def test_import_re2(self):
        expression = '''
        RegularExpressions: import
        RegularExpressions.Node({'a': 1}).match('abc')'''
        expected_output = True  # TODO apparently 1 == True, not sure this works fine
        self._test(expression, expected_output)

    def test_import_re_failed1(self):
        expression = '''
        RegularExpressions: import
        RegularExpressions.Node({'a': 1}).match('bca')'''
        self._test_failed(expression)

    def test_import_re_failed2(self):
        expression = '''
        RegularExpressions: import
        RegularExpressions.Node({'a': 1}).match('')'''
        self._test_failed(expression)

    def test_import_re_automaton(self):
        expression = '''
        RegularExpressions: import
        input: 'ab'
        {
           RegularExpressions.Automaton([RegularExpressions.Node({'a': 1}),
                                         RegularExpressions.Node({'b': 2})]).match(input)
        }()'''
        self._test(expression, True)
