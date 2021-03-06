import unittest

from src.runtime import call, resolve, attribute, evaluate_module, create_scope, create_number, create_list, create_string, slice, \
    get
from src.util import LazyValue as LV, WRException


class TestRuntime(unittest.TestCase):
    def _test(self, result, expected_result):
        if type(expected_result) is list:
            for r, e in zip(result.raw, expected_result):
                self.assertEquals(r.raw, e)
        else:
            self.assertEquals(result.raw, expected_result)

    def _test_fail(self, result):
        self.assertTrue(type(result.raw) is WRException)

    def test_fail1(self):
        # [][0]
        result = evaluate_module(expression=LV(lambda: attribute(create_number(0), create_list([]))))
        self._test_fail(result)

    def test_fail2(self):
        # f: (){ keyError }
        # f()
        result = evaluate_module(items={'f': LV(lambda: create_scope(expression=LV(lambda: resolve('keyError'))))},
                                 expression=LV(lambda: call(resolve('f'), [])))
        self._test_fail(result)

    def test_e1(self):
        # 1
        result = evaluate_module(expression=LV(lambda: create_number(1)))
        self._test(result, 1)

    def test_e2(self):
        # i: 2
        # i
        result = evaluate_module(items={'i': LV(lambda: create_number(2))},
                                 expression=LV(lambda: resolve('i')))
        self._test(result, 2)

    def test_e3(self):
        # o: {
        #   i: 3
        #   i
        # }
        # i: 1
        # o()
        result = evaluate_module(items={'o': LV(lambda: create_scope(items={'i': LV(lambda: create_number(3))},
                                                                     expression=LV(lambda: resolve('i')))),
                                        'i': LV(lambda: create_number(1))},
                                 expression=LV(lambda: call(resolve('o'), [])))
        self._test(result, 3)

    def test_e4(self):
        # o: {
        #   i: 4
        # }
        # o.i
        result = evaluate_module(items={'o': LV(lambda: create_scope(items={'i': LV(lambda: create_number(4))}))},
                                 expression=LV(lambda: attribute(create_string('i'), resolve('o'))))
        self._test(result, 4)

    def test_e5(self):
        # i: 5
        # {
        #   j: i
        #   j
        # }()
        result = evaluate_module(items={'i': LV(lambda: create_number(5))},
                                 expression=LV(lambda: call((create_scope(items={'j': LV(lambda: resolve('i'))},
                                                                          expression=LV(lambda: resolve('j')))), [])))
        self._test(result, 5)

    def test_e6(self):
        # o: {
        #   m: { self.i }
        #   i: 6
        # }
        # o.m()
        result = evaluate_module(items={'o': LV(lambda: create_scope(items={
            'm': LV(lambda: create_scope(expression=LV(lambda: attribute(create_string('i'), resolve('self'))))),
            'i': LV(lambda: create_number(6)),
        }))}, expression=LV(lambda: call(attribute(create_string('m'), resolve('o')), [])))
        self._test(result, 6)

    def test_e7(self):
        # m: { self.i }
        # {
        #   o: {
        #     m: m
        #     i: 7
        #   }
        #   o.m()
        # }()
        result = evaluate_module(
            items={
                'm': LV(lambda: create_scope(expression=LV(lambda: attribute(create_string('i'), resolve('self')))))
            },
            expression=LV(lambda: call(create_scope(
                items={'o': LV(lambda: create_scope(items={'m': LV(lambda: resolve('m')),
                                                            'i': LV(lambda: create_number(7))}))},
                expression=LV(lambda: call(attribute(create_string('m'), resolve('o')), []))), []))
        )
        self._test(result, 7)

    def test_e8(self):
        # m: { self.i }
        # {
        #   o: {
        #     m: m
        #     i: 8
        #   }
        #   {
        #     m: o.m
        #     m()
        #   }()
        # }()
        result = evaluate_module(
            items={
                'm': LV(lambda: create_scope(expression=LV(lambda: attribute(create_string('i'), resolve('self')))))
            },
            expression=LV(lambda: call(create_scope(
                items={'o': LV(lambda: create_scope(items={'m': LV(lambda: resolve('m')),
                                                            'i': LV(lambda: create_number(8))}))},
                expression=LV(lambda: call(create_scope(
                    items={'m': LV(lambda: attribute(create_string('m'), resolve('o')))},
                    expression=LV(lambda: call(resolve('m'), []))), []))), []))
        )
        self._test(result, 8)

    def test_e9(self):
        # f: (a){ a }
        # f(9)
        result = evaluate_module(items={'f': LV(lambda: create_scope(expression=LV(lambda: resolve('a')),
                                                                     defaults=[('a', None)]))},
                                 expression=LV(lambda: call(resolve('f'), [(None, LV(lambda: create_number(9)))])))
        self._test(result, 9)

    def test_e10(self):
        # f: (a: 10){ a }
        # f()
        result = evaluate_module(items={'f': LV(lambda: create_scope(expression=LV(lambda: resolve('a')),
                                                                     defaults=[
                                                                          ('a', LV(lambda: create_number(10)))]))},
                                 expression=LV(lambda: call(resolve('f'), [])))
        self._test(result, 10)

    def test_e11(self):
        # f: (a){
        #   v: a
        #   v
        # }
        # f(11)
        result = evaluate_module(items={'f': LV(lambda: create_scope(items={'v': LV(lambda: resolve('a'))},
                                                                     expression=LV(lambda: resolve('v')),
                                                                     defaults=[('a', None)]))},
                                 expression=LV(lambda: call(resolve('f'), [(None, LV(lambda: create_number(11)))])))
        self._test(result, 11)

    def test_e12(self):
        # sum: (list){
        #   (list[0] + me(list[1:]) or 0
        # }
        # sum([3, 3, 3, 3])
        result = evaluate_module(
            items={'sum': LV(lambda: create_scope(
                defaults=[('list', None)],
                expression=LV(lambda: call(attribute(create_string('or'), call(
                    attribute(create_string('+'), get(create_number(0), resolve('list'))),
                    [(None, LV(lambda: call(
                        resolve('me'),
                        [(None, LV(lambda: slice(resolve('list'), 1)))]
                    )))]
                )), [(None, LV(lambda: create_number(0)))]))
            ))},
            expression=LV(lambda: call(resolve('sum'), [(None, LV(lambda: create_list([create_number(3),
                                                                                       create_number(3),
                                                                                       create_number(3),
                                                                                       create_number(3)])))])))
        self._test(result, 12)

    @unittest.skip  # TODO figure out if this is a problem
    def test_12_infinite_recursion(self):
        # sum: (list){
        #   (me(list[1:] + list[0]) or 0
        # }
        # sum([4, 8])
        # this fails because slicing never fails, so instead of calling the
        # failing term list[0] and breaking out we just infinitely call [][1:]
        result = evaluate_module(
            items={'sum': LV(lambda: create_scope(
                defaults=[('list', None)],
                expression=LV(lambda: call(attribute(create_string('or'), call(
                    attribute(create_string('+'), call(
                        resolve('me'),
                        [(None, LV(lambda: slice(resolve('list'), 1)))]
                    )),
                    [(None, LV(lambda: attribute(create_number(0), resolve('list'))))]
                )), [(None, LV(lambda: create_number(0)))]))
            ))},
            expression=LV(lambda: call(resolve('sum'),
                                       [(None, LV(lambda: create_list([create_number(4), create_number(8)])))])))
        self._test(result, 12)

    def test_e13(self):
        # 6 + 7
        result = evaluate_module(
            expression=LV(
                lambda: call(attribute(create_string('+'), create_number(6)), [(None, LV(lambda: create_number(7)))])))
        self._test(result, 13)

    def test_e14(self):
        # 14 or 0
        result = evaluate_module(
            expression=LV(
                lambda: call(attribute(create_string('or'), create_number(14)), [(None, LV(lambda: create_number(0)))])))
        self._test(result, 14)

    def test_map(self):
        # wrapper: (list){
        #   map: (f){
        #     map: (list){
        #       ([f(list[0])] + me(list[1:])) or []
        #     }
        #     map(list)
        #   }
        # }
        # wrapper([0, 3, 2, 1]).map((e){ e + 1 })
        result = evaluate_module(items={
            'wrapper': LV(lambda: create_scope(defaults=[('list', None)], items={
                'map': LV(lambda: create_scope(defaults=[('f', None)], items={
                    'map': LV(lambda: create_scope(
                        defaults=[('list', None)],
                        expression=LV(lambda: call(attribute(create_string('or'), call(
                            attribute(create_string('+'),
                                      create_list([call(resolve('f'),
                                                        [(None, LV(lambda: attribute(create_number(0), resolve('list'))))])])),
                            [(None, LV(lambda: call(
                                resolve('me'),
                                [(None, LV(lambda: slice(resolve('list'), 1)))]
                            )))]
                        )), [(None, LV(lambda: create_list([])))])))),
                }, expression=LV(lambda: call(resolve('map'), [(None, LV(lambda: resolve('list')))]))))
            }), )
        }, expression=LV(
            lambda: call(
                attribute(create_string('map'), call(resolve('wrapper'), [(None, LV(lambda: create_list([create_number(0),
                                                                                                         create_number(3),
                                                                                                         create_number(2),
                                                                                                         create_number(1)])))])),
                [(None, LV(lambda: create_scope(defaults=[('e', None)],
                                                expression=LV(lambda: call(attribute(create_string('+'), resolve('e')), [
                                                     (None, LV(lambda: create_number(1)))])))))])))
        self._test(result, [1, 4, 3, 2])

    def test_constructor(self):
        # O: (v){
        #   m: (){ v }
        # }
        # O(1).m()
        result = evaluate_module(items={'O': LV(lambda: create_scope(
            defaults=[('v', None)],
            items={'m': LV(lambda: create_scope(expression=LV(lambda: resolve('v'))))}
        ))}, expression=LV(
            lambda: call(attribute(create_string('m'), call(resolve('O'), [(None, LV(lambda: create_number(1)))])), [])))
        self._test(result, 1)

    def test_simple_map(self):
        # f: (e){ e + 1 }
        # {
        #   map: (list){
        #     ([f(list[0])] + me(list[1:])) or []
        #   }
        #   map([0, 1, 2])
        # }()
        result = evaluate_module(items={
            'f': LV(lambda: create_scope(
                defaults=[('e', None)],
                expression=LV(
                    lambda: call(attribute(create_string('+'), resolve('e')), [(None, LV(lambda: create_number(1)))])))),
        }, expression=LV(lambda: call(create_scope(items={
            'map': LV(lambda: create_scope(
                defaults=[('list', None)],
                expression=LV(lambda: call(attribute(create_string('or'), call(
                    attribute(create_string('+'), create_list(
                        [call(resolve('f'), [(None, LV(lambda: attribute(create_number(0), resolve('list'))))])])),
                    [(None, LV(lambda: call(
                        resolve('me'),
                        [(None, LV(lambda: slice(resolve('list'), 1)))]
                    )))]
                )), [(None, LV(lambda: create_list([])))])))),
        }, expression=LV(lambda: call(resolve('map'), [(None, LV(lambda: create_list([create_number(0),
                                                                                      create_number(1),
                                                                                      create_number(2)])))]))), [])))
        self._test(result, [1, 2, 3])

    def test_simple_map_empty(self):
        # f: (e){ e + 1 }
        # {
        #   map: (list){
        #     ([f(list[0])] + me(list[1:])) or []
        #   }
        #   map([])
        # }()
        result = evaluate_module(items={
            'f': LV(lambda: create_scope(
                defaults=[('e', None)],
                expression=LV(
                    lambda: call(attribute(create_string('+'), resolve('e')), [(None, LV(lambda: create_number(1)))])))),
        }, expression=LV(lambda: call(create_scope(items={
            'map': LV(lambda: create_scope(
                defaults=[('list', None)],
                expression=LV(lambda: call(attribute(create_string('or'), call(
                    attribute(create_string('+'), create_list(
                        [call(resolve('f'), [(None, LV(lambda: attribute(create_number(0), resolve('list'))))])])),
                    [(None, LV(lambda: call(
                        resolve('me'),
                        [(None, LV(lambda: slice(resolve('list'), 1)))]
                    )))]
                )), [(None, LV(lambda: create_list([])))])))),
        }, expression=LV(lambda: call(resolve('map'), [(None, LV(lambda: create_list([])))]))), [])))
        self._test(result, [])

    def test_list_length1(self):
        # [].length()
        result = evaluate_module(
            expression=LV(lambda: call(attribute(create_string('length'), create_list([])), [])))
        self._test(result, 0)

    def test_list_length2(self):
        # [0, 1, 2].length()
        result = evaluate_module(
            expression=LV(lambda: call(attribute(create_string('length'), create_list([create_number(0),
                                                                                       create_number(1),
                                                                                       create_number(2)])), [])))
        self._test(result, 3)

    def test_dict_length1(self):
        # {}.length()
        result = evaluate_module(
            expression=LV(lambda: call(attribute(create_string('length'), create_scope()), [])))
        self._test(result, 0)

    def test_dict_length2(self):
        # {a: 1
        #  b: 2}.length()
        result = evaluate_module(
            expression=LV(lambda: call(attribute(create_string('length'), create_scope(items={'a': None, 'b': None})), [])))
        self._test(result, 2)

    def test_string_lenght1(self):
        # ''.length()
        result = evaluate_module(
            expression=LV(lambda: call(attribute(create_string('length'), create_string('')), [])))
        self._test(result, 0)

    def test_string_lenght2(self):
        # 'abc'.length()
        result = evaluate_module(
            expression=LV(lambda: call(attribute(create_string('length'), create_string('abc')), [])))
        self._test(result, 3)

    def test_expression_get1(self):
        # {a: 1}['a']
        result = evaluate_module(
            expression=LV(lambda: attribute(create_string('a'), create_scope(items={'a': LV(lambda: create_number(1))}))))
        self._test(result, 1)

    def test_expression_get2(self):
        # A: {a: 2}
        # B: {b: 'a'}
        # A[B['b']]
        result = evaluate_module(
            items={'A': LV(lambda: create_scope(items={'a': LV(lambda: create_number(2))})),
                   'B': LV(lambda: create_scope(items={'b': LV(lambda: create_string('a'))}))},
            expression=LV(lambda: attribute(attribute(create_string('b'), resolve('B')), resolve('A'))))
        self._test(result, 2)

    def test_string_add(self):
        # 'a' + 'b'
        result = evaluate_module(
            expression=LV(lambda: call(attribute(create_string('+'), create_string('a')), [(None, LV(lambda: create_string('b')))])))
        self._test(result, 'ab')

    def test_string_slice(self):
        # 'abc'[1:]
        result = evaluate_module(
            expression=LV(lambda: slice(create_string('abc'), 1)))
        self._test(result, 'bc')
