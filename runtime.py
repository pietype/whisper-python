from util import logger, Object, WRException, LazyValue as LV


# TODO patchwork, needs refactoring
def evaluate(node):
    if node is None:  # no expression in object
        # logger.debug('create object')
        return scope_stack[-1]

    command = node[0]

    if command == 'call':
        function = node[1]
        arguments = node[2]

        # things evaluate in the wrong order inside comprehension
        _args = []
        for i, e in arguments:
            def _make_lambda(e):
                def _lambda():
                    return evaluate(e)
                return _lambda
            _args.append((evaluate(i) if i else None, LV(_make_lambda(e))))
        return call(evaluate(function), _args)

    if command == 'create_dict':
        defaults = node[1]
        items = node[2]
        expression = node[3]
        return create_object(defaults=[(evaluate(i).raw, LV(lambda: evaluate(e)) if e else None) for i, e in defaults],
                             items=dict([(evaluate(k).raw, LV(lambda: evaluate(v))) for k, v in items.items()]),
                             expression=LV(lambda: evaluate(expression)))

    if command == 'create_number':
        native = node[1]
        return create_number(native)

    if command == 'create_string':
        native = node[1]
        return create_string(native)

    if command == 'create_list':
        native = node[1]
        evaluated = [evaluate(n) for n in native]
        return create_list(evaluated)

    if command == 'get':
        object = node[1]
        item = node[2]
        return get(evaluate(item), evaluate(object))

    if command == 'infix_chain':
        # TODO operator priority
        l = node[1]
        o = l[0][1]
        for ident, argument in l[1:]:
            o = ('call', ('resolve', ident, o), [(None, argument)])

        return evaluate(o)

    if command == 'resolve':
        item = node[1]
        object = node[2]
        if object is None:
            return resolve(evaluate(item).raw)
        else:  # get
            return get(evaluate(item), evaluate(object))

    if command == 'slice':
        object = node[1]
        _from = node[2]
        _to = node[3]
        return slice(evaluate(object), evaluate(_from).raw, evaluate(_to).raw if _to else None)

    raise Exception('Unknown command: %s' % command)
## TODO end patchwork


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


def get(object, scope):
    logger.debug('get {} in {}'.format(object.raw, scope._id))
    value = object.raw
    if value in scope.items:
        output = _new_with_self(_expression_with_scope(scope.items[value], lambda: _item_resolution_scope(scope))(), scope)
        logger.debug('get returned {}'.format(output._id))
        return output
    try:
        return _at_index(value, scope)
    except:  # all the bad things that happen when you do not_a_list[not_a_number] in python
        pass

    return create_failed(WRException('Attribute error: `%s`' % value))


def _at_index(index, list):
    try:
        return list.raw[index]
    except IndexError as e:
        return create_failed(WRException('Index out of range: %s' % index))


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

    logger.debug('arguments scope {} (for {})'.format(output._id, prototype._id))
    return output


def _new_with_self(prototype, self):
    output = Object(prototype=prototype)
    output.self = self

    logger.debug('self scope {} (for {})'.format(output._id, prototype._id))
    return output


def _item_resolution_scope(scope):
    output = Object(prototype=scope)
    output._can_resolve_items = False
    # output.parent = scope

    logger.debug('item resolution scope {} (for {})'.format(output._id, scope._id))
    return output


def _argument_resolution_scope(scope):
    return scope.parent


def _arguments(arguments, defaults):
    if not arguments:
        return {}

    output = dict([(defaults[0][0], arguments[0][1])] + arguments[1:])
    return output


def create_object(defaults=[], items={}, expression=None):
    output = create_dict(items)

    output.defaults = defaults
    output.items.update(items)
    output.expression = expression
    output.parent = scope_stack[-1]
    output.arguments_scope = output.parent

    logger.debug('create object {} {} {} (parent {})'.format(output._id, defaults, items, output.parent._id))
    return output


_native_cache = {}
def _create_native(value):
    try:
        if value in _native_cache:
            return _native_cache[value]
    except TypeError:  # unhashable type
        pass

    output = Object()
    output.items = {
        '+': LV(lambda: create_object(
            defaults=[('other', None)],
            expression=LV(lambda: _native_add(resolve('self'), resolve('other')))
        )),
        'or': LV(lambda: create_object(
            defaults=[('other', None)],
            expression=LV(lambda: resolve('self'))
        )),
    }
    output.parent = scope_stack[0]
    output.arguments_scope = output.parent
    output.raw = value

    try:
        _native_cache[value] = output
    except TypeError:  # unhashable type
        pass

    logger.debug('create native {} {}'.format(output._id, value))
    return output


def create_number(native):
    output = _create_native(native)
    output.items.update({

    })
    return output


def create_string(native):
    output = _create_native(native)
    output.items.update({
        'length': LV(lambda: create_object(
            expression=LV(lambda: _native_length(resolve('self')))
        )),
    })
    return output


def create_list(native):
    for e in native:
        if type(e.raw) is WRException:
            return e
    output = _create_native(native)
    output.items.update({
        'length': LV(lambda: create_object(
            expression=LV(lambda: _native_length(resolve('self')))
        )),

        'map': LV(lambda: create_object(
            defaults=[('function', None)],
            expression=LV(lambda: call(get(create_string('or'), call(
                get(create_string('+'), create_list(
                    [call(resolve('function'), [(None, LV(lambda: get(create_number(0), resolve('self'))))])])),
                [(None, LV(lambda: call(
                    get(create_string('map'), slice(resolve('self'), 1)),
                    [(None, LV(lambda: resolve('function')))]
                )))]
            )), [(None, LV(lambda: create_list([])))])))),
    })
    return output


def create_dict(native):
    output = _create_native(native)
    output.items.update({
        'length': LV(lambda: create_object(
            expression=LV(lambda: _native_length(resolve('self')))
        )),
    })
    return output


def create_failed(value):
    output = _create_native(value)
    output.items = {
        'or': LV(lambda: create_object(
            defaults=[('other', None)],
            expression=LV(lambda: resolve('other'))
        )),
    }

    return output


def _native_length(o):
    return create_number(len(o.raw))


def _native_add(a, b):
    return create_number(a.raw + b.raw)


def evaluate_module(items={}, expression=None):
    module = create_object(items=items, expression=expression)

    return call(module, [])


# bootstrap scope_stack
scope_stack = []
root = Object()
scope_stack.append(root)
