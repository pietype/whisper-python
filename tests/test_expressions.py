from unittest import TestCase

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

    def test_define_argument_default1(self):
        e = '''
        f: (a: 5){ a }
        f()'''
        self._test(e, 5)

    def test_define_argument_default2(self):
        e = '''
        f: (a, b: 1){ a + b }
        f(5)'''
        self._test(e, 6)

    def test_define_argument_default3(self):
        e = '''
        f: (a, b: 1){ a + b }
        f(5, b: 2)'''
        self._test(e, 7)

    def test_define_object_static1(self):
        e = '''
        o: (){
          m: (){ 5 }
        }
        o.m()'''
        self._test(e, 5)

    def test_constructor(self):
        e = '''
        O: (v){
          m: (){ v }
        }
        O(1).m()'''
        self._test(e, 1)

    def test_then(self):
        e = '''
        1 then (n){ n + 1 }'''
        self._test(e, 2)

    def test_then_failed(self):
        e = '''
        [][0] then (){ 1 }'''
        self._test_failed(e)


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

    def test_length(self):
        e = '''
        "abc".length()'''
        self._test(e, 3)

    def test_get1(self):
        e = '''
        "ab"[0]'''
        self._test(e, 'a')

    def test_get2(self):
        e = '''
        "ab"[1]'''
        self._test(e, 'b')

    def test_get_expression(self):
        e = '''
        "abc"[1 + 1]'''
        self._test(e, 'c')


class TestNumber(TestBase):
    def test_add1(self):
        e = '''
        1.+(1)'''
        self._test(e, 2)

    def test_add1_infix(self):
        e = '''
        1 + 2'''
        self._test(e, 3)

    def test_equal1_infix(self):
        e = '1 = 1'
        self._test(e, True)


class TestDictionary(TestBase):
    def test_create1(self):
        e = '''
        {}'''
        self._test(e, {})

    def test_get1(self):
        e = '''
        {'a': 1}['a']'''
        self._test(e, 1)

    # def test_dynamic_get(self):


class TestScoping(TestBase):
    def test_argument_accessibility1(self):
        e = '''
        f: (a){
          b: a
          b
        }
        f(1)'''
        self._test(e, 1)

    def test_argument_accessibility2(self):
        e = '''
        f: (a){
          g: (b){
            c: b
            c
          }
          g(a)
        }
        f(1)'''
        self._test(e, 1)

    def test_argument_accessibility3(self):
        e = '''
        f: (a){
          g: (b){
            h: (b){
              c: a + b  # a needs to be available
              a + c
            }
            h(b)
          }
          g(a)
        }

        f(2)'''
        self._test(e, 6)

    def test_item_resolution1(self):
        e = '''
        m: 1
        (){
          m: m
          m
        }()'''
        self._test(e, 1)

    def test_item_resolution2(self):
        e = '''
        m: 1
        (){
          m: m
        }.m'''
        self._test(e, 1)

    def test_item_accessibility1(self):
        e = '''f: (a){
          a + 1
        }

        (){
          g: (a){
            f(a) + 1
          }
          g(1)
        }()'''
        self._test(e, 3)

    # def test_constructor(self):
    #     e = '''
    #     o: (a){
    #       m: (){ a }
    #     }
    #
    #     [o(0), o(1)][1].m()
    #     '''
    #     self._test(e, 1)


class Experimental(TestBase):
    def test_import_re_automaton1(self):
        e = '''
        RegularExpressions: import
        RegularExpressions.Automaton([{'a': 1}]).match('a')'''
        self._test(e, 1)

    def test_import_re_automaton2(self):
        e = '''
        RegularExpressions: import
        RegularExpressions.Automaton([{'a': 1},
                                      {'b': 2}]).match('ab')'''
        self._test(e, 2)
