import os

from parser import WhisperParser
from util import logger, Object, WRException, LazyValue as LV, _partial
from core import modules


_parser = WhisperParser()


# TODO patchwork, needs refactoring
def evaluate(node):
    if node is None:  # no expression in object
        # logger.debug('create object')
        return scope_stack[-1]

    command = node[0]

    if command == 'call':
        function, arguments = node[1:]

        # things evaluate in the wrong order inside a comprehension
        _args = []
        for i, e in arguments:
            _args.append((evaluate(i).raw if i else None, LV(_partial(evaluate, e))))
        return call(evaluate(function), _args)

    if command == 'create_dictionary':
        native = node[1]
        evaluated = dict([(evaluate(k).raw, evaluate(v)) for k, v in native])
        return create_dictionary(evaluated)

    if command == 'create_list':
        native = node[1]
        evaluated = [evaluate(n) for n in native]
        return create_list(evaluated)

    if command == 'create_number':
        native = node[1]
        return create_number(native)

    if command == 'create_string':
        native = node[1]
        return create_string(native)

    if command == 'create_scope':
        defaults, items, expression = node[1:]

        return create_scope(defaults=[(evaluate(i).raw, LV(_partial(evaluate, e)) if e else None) for i, e in defaults],
                            items=dict([(evaluate(k).raw, LV(_partial(evaluate, v))) for k, v in items.items()]),
                            expression=LV(_partial(evaluate, expression)))

    if command == 'get':
        object, item = node[1:]
        return get(evaluate(item), evaluate(object))

    if command == 'import':
        path = node[1]
        return evaluate(_import(evaluate(path)))

    if command == 'infix_chain':
        # TODO operator priority
        l = node[1]
        o = l[0][1]
        for ident, argument in l[1:]:
            o = ('call', ('resolve', ident, o), [(None, argument)])

        return evaluate(o)

    if command == 'resolve':
        item, object = node[1:]
        if object is None:
            return resolve(evaluate(item).raw)
        else:  # get
            return attribute(evaluate(item), evaluate(object))

    if command == 'slice':
        object, _from, _to = node[1:]
        return slice(evaluate(object), evaluate(_from).raw, evaluate(_to).raw if _to else None)

    raise Exception('Unknown command: %s' % command)
# TODO end patchwork


def call(function, arguments):
    logger.debug("call {} {}".format(function._id, arguments))
    scope_with_arguments = _new_with_arguments(function, arguments, scope_stack[-1])

    if scope_with_arguments.expression:
        scope_stack.append(scope_with_arguments)
        output = scope_with_arguments.expression()
        scope_stack.pop()
    else:
        output = scope_with_arguments

    output.stack_trace.append(scope_with_arguments)
    logger.debug("return {} (from {})".format(output._id, function._id))
    return output


def _expression_with_scope(expression, scope):
    def output():
        scope_stack.append(scope())
        output = expression()
        scope_stack.pop()

        return output
    return output


def _get_scope_dict(scope):
    output = {
        'me': lambda: scope,
        'parent': lambda: scope.parent,
        'self': lambda: scope.self,
    }

    for k, e in dict(scope.defaults).items():
        if k in _arguments(scope.arguments, scope.defaults):
            _e = _arguments(scope.arguments, scope.defaults)[k]
            _s = lambda: scope.arguments_scope
        else:
            _e = e
            _s = lambda: scope.parent
        output[k] = _expression_with_scope(_e, _s)

    if scope._can_resolve_items:
        for k, e in scope.items.items():
            output[k] = _expression_with_scope(e, lambda: _item_resolution_scope(scope))

    return output


def _resolve(ident, scope):
    logger.debug("resolve {} (in {})".format(ident, scope._id))

    d = _get_scope_dict(scope)
    if ident in d:
        return d[ident]()

    if scope.parent:
        return _resolve(ident, scope.parent)

    return create_failed(WRException('Key error: `%s`' % ident))


def resolve(ident):
    scope = scope_stack[-1]
    output = _resolve(ident, scope)
    logger.debug('resolved {} to {}'.format(ident, output._id))
    return output


def attribute(object, scope):
    value = object.raw
    if value in scope.items:
        output = _new_with_self(_expression_with_scope(scope.items[value], lambda: _item_resolution_scope(scope))(), scope)
        logger.debug('attribute {} in {}, returned {}'.format(object.raw, scope._id, output._id))
        return output

    return create_failed(WRException('Attribute error: `%s`' % value))


def get(object, gettable):
    try:
        index = object.raw
        native = gettable.raw
        output = native[index]
        # hack handle native string get
        if type(output) is str:
            output = create_string(output)
        logger.debug('get {} in {}, returned {}'.format(object.raw, gettable._id, output._id))
        return output
    except IndexError as e:
        return create_failed(WRException('Index out of range: %s' % index))
    except KeyError as e:
        return create_failed(WRException('Key error: %s' % index))


def slice(list, _from, _to=None):
    _to = _to or len(list.raw)
    # TODO hack because there's no iterable yet for slice to work on
    native = list.raw[_from:_to]
    if type(native) is str:
        return create_string(native)
    return create_list(native)


def _new_with_arguments(prototype, arguments, arguments_scope):
    if prototype.arguments == arguments and prototype.arguments_scope == arguments_scope:
        return prototype
    output = Object(prototype=prototype)
    output.arguments = arguments
    output.arguments_scope = arguments_scope

    # logger.debug('arguments scope {} (for {})'.format(output._id, prototype._id))
    return output


def _new_with_self(prototype, self):
    output = Object(prototype=prototype)
    output.self = self

    # logger.debug('self scope {} (for {})'.format(output._id, prototype._id))
    return output


def _item_resolution_scope(scope):
    output = Object(prototype=scope)
    output._can_resolve_items = False
    # output.parent = scope

    # logger.debug('item resolution scope {} (for {})'.format(output._id, scope._id))
    return output


def _argument_resolution_scope(scope):
    return scope.parent


def _arguments(arguments, defaults):
    if not arguments:
        return {}

    output = dict([(defaults[0][0], arguments[0][1])] + arguments[1:])
    return output


def create_scope(defaults=[], items={}, expression=None):
    output = create_dictionary(items)

    output.defaults = defaults
    output.items.update(items)
    output.expression = expression
    output.parent = scope_stack[-1]
    output.arguments_scope = output.parent

    # logger.debug('create scope {} {} {} (parent {})'.format(output._id, defaults, items, output.parent._id))
    return output


def _create_native(value):
    output = Object()
    output.items = {
        'or': LV(lambda: create_scope(
            defaults=[('other', None)],
            expression=LV(lambda: resolve('self'))
        )),
        'then': LV(lambda: create_scope(
            defaults=[('callable', None)],
            expression=LV(lambda: call(resolve('callable'), [(None, LV(lambda: resolve('self')))]))
        )),
    }
    output.parent = scope_stack[0]
    output.arguments_scope = output.parent
    output.raw = value

    logger.debug('create native {} {}'.format(output._id, value))
    return output


def create_number(native):
    output = _create_native(native)
    output.items.update({
        '+': LV(lambda: create_scope(
            defaults=[('other', None)],
            expression=LV(lambda: _native_add(resolve('self'), resolve('other')))
        )),
        '=': LV(lambda: create_scope(
            defaults=[('other', None)],
            expression=LV(lambda: _native_equals(resolve('self'), resolve('other')))
        )),
    })
    return output


def create_string(native):
    output = _create_native(native)
    output.items.update({
        'length': LV(lambda: create_scope(
            expression=LV(lambda: _native_length(resolve('self')))
        )),
        '+': LV(lambda: create_scope(
            defaults=[('other', None)],
            expression=LV(lambda: _native_add(resolve('self'), resolve('other')))
        )),
    })
    return output


def create_list(native):
    for e in native:
        if type(e.raw) is WRException:
            return e
    output = _create_native(native)
    output.items.update({
        '+': LV(lambda: create_scope(
            defaults=[('other', None)],
            expression=LV(lambda: _native_add(resolve('self'), resolve('other')))
        )),
        'length': LV(lambda: create_scope(
            expression=LV(lambda: _native_length(resolve('self')))
        )),
        'map': LV(lambda: create_scope(
            defaults=[('function', None)],
            expression=LV(lambda: call(attribute(create_string('or'), call(
                attribute(create_string('+'), create_list(
                    [call(resolve('function'), [(None, LV(lambda: get(create_number(0), resolve('self'))))])])),
                [(None, LV(lambda: call(
                    attribute(create_string('map'), slice(resolve('self'), 1)),
                    [(None, LV(lambda: resolve('function')))]
                )))]
            )), [(None, LV(lambda: create_list([])))])))),
        # reduce: (f){
        #   f(self[0])(self[1:].reduce(f)) or self[0]
        # }
        'reduce': LV(lambda: create_scope(
            defaults=[('function', None)],
            expression=LV(lambda: call(
                attribute(create_string('or'),
                          call(call(resolve('function'),
                                    [(None, LV(lambda: get(create_number(0), resolve('self'))))]),
                               [(None, LV(lambda: call(
                             attribute(create_string('reduce'),
                                       slice(resolve('self'), 1)),
                             [(None, LV(lambda: resolve('function')))])))])),
                [(None, LV(lambda: get(create_number(0), resolve('self'))))])))),
    })
    return output


def create_dictionary(native):
    output = _create_native(native)
    output.items.update({
        'length': LV(lambda: create_scope(
            expression=LV(lambda: _native_length(resolve('self')))
        )),
    })
    return output


def create_failed(value):
    output = _create_native(value)
    output.items = {
        'or': LV(lambda: create_scope(
            defaults=[('other', None)],
            expression=LV(lambda: resolve('other'))
        )),
        'then': LV(lambda: resolve('self')),
    }

    return output


def _native_length(o):
    return create_number(len(o.raw))


def _native_add(a, b):
    try:
        native = a.raw + b.raw
        return {
            int: create_number,
            list: create_list,
            str: create_string,
        }[type(native)](native)
    except Exception as e:
        logger.debug(e)  # TODO narrow down exception list
        return create_failed(WRException('Cannot add types: %s, %s' % (type(a.raw), type(b.raw))))


def _native_equals(a, b):
    try:
        if a.raw == b.raw:
            return a  # or b
        return create_failed(False)
    except Exception as e:
        logger.debug(e)  # TODO narrow down exceptions
        return create_failed(e)


def evaluate_module(items={}, expression=None):
    module = create_scope(items=items, expression=expression)

    return call(module, [])


_import_cache = {}
def _import(path):
    if path.raw in _import_cache:
        return _import_cache[path.raw]
    try:
        source = modules[path.raw]
        node = _parser.parse(source)
        _import_cache[path] = node
        return node
    except KeyError as e:
        return create_failed("No such module: {}".format(path.raw))


# bootstrap scope_stack
scope_stack = []
root = Object()
scope_stack.append(root)
