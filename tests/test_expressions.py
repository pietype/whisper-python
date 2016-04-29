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


class TestString(TestBase):
    def test_slice1(self):
        e = '''
        'abc'[1:]'''
        self._test(e, 'bc')


# class Experimental(TestBase):
