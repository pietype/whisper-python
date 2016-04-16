from unittest import TestCase

from parser import WhisperParser
from runtime import evaluate


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


class TestString(TestBase):
    def test_slice1(self):
        e = '''
        'abc'[1:]'''
        self._test(e, 'bc')
