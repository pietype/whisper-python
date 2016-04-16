import unittest

from runtime import call, resolve, get, evaluate_module, create_object, create_native, slice
from util import LV, WRException


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
        result = evaluate_module(expression=LV(lambda: get(create_native(create_native(0)), create_native([]))))
        self._test_fail(result)

    def test_fail2(self):
        # f: (){ keyError }
        # f()
        result = evaluate_module(items={'f': LV(lambda: create_object(expression=LV(lambda: resolve('keyError'))))},
                                 expression=LV(lambda: call(resolve('f'), [])))
        self._test_fail(result)

    def test_e1(self):
        # 1
        result = evaluate_module(expression=LV(lambda: create_native(1)))
        self._test(result, 1)

    def test_e2(self):
        # i: 2
        # i
        result = evaluate_module(items={'i': LV(lambda: create_native(2))},
                                 expression=LV(lambda: resolve('i')))
        self._test(result, 2)

    def test_e3(self):
        # o: {
        #   i: 3
        #   i
        # }
        # i: 1
        # o()
        result = evaluate_module(items={'o': LV(lambda: create_object(items={'i': LV(lambda: create_native(3))},
                                                                      expression=LV(lambda: resolve('i')))),
                                        'i': LV(lambda: create_native(1))},
                                 expression=LV(lambda: call(resolve('o'), [])))
        self._test(result, 3)

    def test_e4(self):
        # o: {
        #   i: 4
        # }
        # o.i
        result = evaluate_module(items={'o': LV(lambda: create_object(items={'i': LV(lambda: create_native(4))}))},
                                 expression=LV(lambda: get(create_native('i'), resolve('o'))))
        self._test(result, 4)

    def test_e5(self):
        # i: 5
        # {
        #   j: i
        #   j
        # }()
        result = evaluate_module(items={'i': LV(lambda: create_native(5))},
                                 expression=LV(lambda: call((create_object(items={'j': LV(lambda: resolve('i'))},
                                                                           expression=LV(lambda: resolve('j')))), [])))
        self._test(result, 5)

    def test_e6(self):
        # o: {
        #   m: { self.i }
        #   i: 6
        # }
        # o.m()
        result = evaluate_module(items={'o': LV(lambda: create_object(items={
            'm': LV(lambda: create_object(expression=LV(lambda: get(create_native('i'), resolve('self'))))),
            'i': LV(lambda: create_native(6)),
        }))}, expression=LV(lambda: call(get(create_native('m'), resolve('o')), [])))
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
                'm': LV(lambda: create_object(expression=LV(lambda: get(create_native('i'), resolve('self')))))
            },
            expression=LV(lambda: call(create_object(
                items={'o': LV(lambda: create_object(items={'m': LV(lambda: resolve('m')),
                                                            'i': LV(lambda: create_native(7))}))},
                expression=LV(lambda: call(get(create_native('m'), resolve('o')), []))), []))
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
                'm': LV(lambda: create_object(expression=LV(lambda: get(create_native('i'), resolve('self')))))
            },
            expression=LV(lambda: call(create_object(
                items={'o': LV(lambda: create_object(items={'m': LV(lambda: resolve('m')),
                                                            'i': LV(lambda: create_native(8))}))},
                expression=LV(lambda: call(create_object(
                    items={'m': LV(lambda: get(create_native('m'), resolve('o')))},
                    expression=LV(lambda: call(resolve('m'), []))), []))), []))
        )
        self._test(result, 8)

    def test_e9(self):
        # f: (a){ a }
        # f(9)
        result = evaluate_module(items={'f': LV(lambda: create_object(expression=LV(lambda: resolve('a')),
                                                                      defaults=[('a', None)]))},
                                 expression=LV(lambda: call(resolve('f'), [(None, LV(lambda: create_native(9)))])))
        self._test(result, 9)

    def test_e10(self):
        # f: (a: 10){ a }
        # f()
        result = evaluate_module(items={'f': LV(lambda: create_object(expression=LV(lambda: resolve('a')),
                                                                      defaults=[
                                                                          ('a', LV(lambda: create_native(10)))]))},
                                 expression=LV(lambda: call(resolve('f'), [])))
        self._test(result, 10)

    def test_e11(self):
        # f: (a){
        #   v: a
        #   v
        # }
        # f(11)
        result = evaluate_module(items={'f': LV(lambda: create_object(items={'v': LV(lambda: resolve('a'))},
                                                                      expression=LV(lambda: resolve('v')),
                                                                      defaults=[('a', None)]))},
                                 expression=LV(lambda: call(resolve('f'), [(None, LV(lambda: create_native(11)))])))
        self._test(result, 11)

    def test_e12(self):
        # sum: (list){
        #   (list[0] + me(list[1:]) or 0
        # }
        # sum([3, 3, 3, 3])
        result = evaluate_module(
            items={'sum': LV(lambda: create_object(
                defaults=[('list', None)],
                expression=LV(lambda: call(get(create_native('or'), call(
                    get(create_native('+'), get(create_native(0), resolve('list'))),
                    [(None, LV(lambda: call(
                        resolve('me'),
                        [(None, LV(lambda: slice(resolve('list'), 1)))]
                    )))]
                )), [(None, LV(lambda: create_native(0)))]))
            ))},
            expression=LV(lambda: call(resolve('sum'), [(None, LV(lambda: create_native([create_native(3),
                                                                                         create_native(3),
                                                                                         create_native(3),
                                                                                         create_native(3)])))])))
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
            items={'sum': LV(lambda: create_object(
                defaults=[('list', None)],
                expression=LV(lambda: call(get(create_native('or'), call(
                    get(create_native('+'), call(
                        resolve('me'),
                        [(None, LV(lambda: slice(resolve('list'), 1)))]
                    )),
                    [(None, LV(lambda: get(create_native(0), resolve('list'))))]
                )), [(None, LV(lambda: create_native(0)))]))
            ))},
            expression=LV(lambda: call(resolve('sum'),
                                       [(None, LV(lambda: create_native([create_native(4), create_native(8)])))])))
        self._test(result, 12)

    def test_e13(self):
        # 6 + 7
        result = evaluate_module(
            expression=LV(
                lambda: call(get(create_native('+'), create_native(6)), [(None, LV(lambda: create_native(7)))])))
        self._test(result, 13)

    def test_e14(self):
        # 14 or 0
        result = evaluate_module(
            expression=LV(
                lambda: call(get(create_native('or'), create_native(14)), [(None, LV(lambda: create_native(0)))])))
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
            'wrapper': LV(lambda: create_object(defaults=[('list', None)], items={
                'map': LV(lambda: create_object(defaults=[('f', None)], items={
                    'map': LV(lambda: create_object(
                        defaults=[('list', None)],
                        expression=LV(lambda: call(get(create_native('or'), call(
                            get(create_native('+'),
                                create_native([call(resolve('f'),
                                                    [(None, LV(lambda: get(create_native(0), resolve('list'))))])])),
                            [(None, LV(lambda: call(
                                resolve('me'),
                                [(None, LV(lambda: slice(resolve('list'), 1)))]
                            )))]
                        )), [(None, LV(lambda: create_native([])))])))),
                }, expression=LV(lambda: call(resolve('map'), [(None, LV(lambda: resolve('list')))]))))
            }), )
        }, expression=LV(
            lambda: call(
                get(create_native('map'), call(resolve('wrapper'), [(None, LV(lambda: create_native([create_native(0),
                                                                                                     create_native(3),
                                                                                                     create_native(2),
                                                                                                     create_native(
                                                                                                         1)])))])),
                [(None, LV(lambda: create_object(defaults=[('e', None)],
                                                 expression=LV(lambda: call(get(create_native('+'), resolve('e')), [
                                                     (None, LV(lambda: create_native(1)))])))))])))
        self._test(result, [1, 4, 3, 2])

    def test_constructor(self):
        # O: (v){
        #   m: (){ v }
        # }
        # O(1).m()
        result = evaluate_module(items={'O': LV(lambda: create_object(
            defaults=[('v', None)],
            items={'m': LV(lambda: create_object(expression=LV(lambda: resolve('v'))))}
        ))}, expression=LV(
            lambda: call(get(create_native('m'), call(resolve('O'), [(None, LV(lambda: create_native(1)))])), [])))
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
            'f': LV(lambda: create_object(
                defaults=[('e', None)],
                expression=LV(
                    lambda: call(get(create_native('+'), resolve('e')), [(None, LV(lambda: create_native(1)))])))),
        }, expression=LV(lambda: call(create_object(items={
            'map': LV(lambda: create_object(
                defaults=[('list', None)],
                expression=LV(lambda: call(get(create_native('or'), call(
                    get(create_native('+'), create_native(
                        [call(resolve('f'), [(None, LV(lambda: get(create_native(0), resolve('list'))))])])),
                    [(None, LV(lambda: call(
                        resolve('me'),
                        [(None, LV(lambda: slice(resolve('list'), 1)))]
                    )))]
                )), [(None, LV(lambda: create_native([])))])))),
        }, expression=LV(lambda: call(resolve('map'), [(None, LV(lambda: create_native([create_native(0),
                                                                                        create_native(1),
                                                                                        create_native(2)])))]))), [])))
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
            'f': LV(lambda: create_object(
                defaults=[('e', None)],
                expression=LV(
                    lambda: call(get(create_native('+'), resolve('e')), [(None, LV(lambda: create_native(1)))])))),
        }, expression=LV(lambda: call(create_object(items={
            'map': LV(lambda: create_object(
                defaults=[('list', None)],
                expression=LV(lambda: call(get(create_native('or'), call(
                    get(create_native('+'), create_native(
                        [call(resolve('f'), [(None, LV(lambda: get(create_native(0), resolve('list'))))])])),
                    [(None, LV(lambda: call(
                        resolve('me'),
                        [(None, LV(lambda: slice(resolve('list'), 1)))]
                    )))]
                )), [(None, LV(lambda: create_native([])))])))),
        }, expression=LV(lambda: call(resolve('map'), [(None, LV(lambda: create_native([])))]))), [])))
        self._test(result, [])

    def test_list_length1(self):
        # [].length()
        result = evaluate_module(
            expression=LV(lambda: call(get(create_native('length'), create_native([])), [])))
        self._test(result, 0)

    def test_list_length2(self):
        # [0, 1, 2].length()
        result = evaluate_module(
            expression=LV(lambda: call(get(create_native('length'), create_native([create_native(0),
                                                                                   create_native(1),
                                                                                   create_native(2)])), [])))
        self._test(result, 3)

    def test_dict_length1(self):
        # {}.length()
        result = evaluate_module(
            expression=LV(lambda: call(get(create_native('length'), create_object()), [])))
        self._test(result, 0)

    def test_dict_length2(self):
        # {a: 1
        #  b: 2}.length()
        result = evaluate_module(
            expression=LV(lambda: call(get(create_native('length'), create_object(items={'a': None, 'b': None})), [])))
        self._test(result, 2)

    def test_string_lenght1(self):
        # ''.length()
        result = evaluate_module(
            expression=LV(lambda: call(get(create_native('length'), create_native('')), [])))
        self._test(result, 0)

    def test_string_lenght2(self):
        # 'abc'.length()
        result = evaluate_module(
            expression=LV(lambda: call(get(create_native('length'), create_native('abc')), [])))
        self._test(result, 3)

    def test_expression_get1(self):
        # {a: 1}['a']
        result = evaluate_module(
            expression=LV(lambda: get(create_native('a'), create_object(items={'a': LV(lambda: create_native(1))}))))
        self._test(result, 1)

    def test_expression_get2(self):
        # A: {a: 2}
        # B: {b: 'a'}
        # A[B['b']]
        result = evaluate_module(
            items={'A': LV(lambda: create_object(items={'a': LV(lambda: create_native(2))})),
                   'B': LV(lambda: create_object(items={'b': LV(lambda: create_native('a'))}))},
            expression=LV(lambda: get(get(create_native('b'), resolve('B')), resolve('A'))))
        self._test(result, 2)

    def test_string_add(self):
        # 'a' + 'b'
        result = evaluate_module(
            expression=LV(lambda: call(get(create_native('+'), create_native('a')), [(None, LV(lambda: create_native('b')))])))
        self._test(result, 'ab')

    def test_string_slice(self):
        # 'abc'[1:]
        result = evaluate_module(
            expression=LV(lambda: slice(create_native('abc'), 1)))
        self._test(result, 'bc')
