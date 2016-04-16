from util import Object, WRException, LV

scope_stack = []


def call(function, arguments):
    scope_with_arguments = _new_with_arguments(function, arguments, scope_stack[-1])

    if scope_with_arguments.expression:
        scope_stack.append(scope_with_arguments)
        output = scope_with_arguments.expression()
        scope_stack.pop()
    else:
        output = scope_with_arguments

    output.stack_trace.append(scope_with_arguments)
    return output


def _resolve_in_closure(ident, scope):
    if ident in dict(scope.defaults):
        if ident in _arguments(scope.arguments, scope.defaults):
            expression_scope = scope.arguments_scope
            expression = _arguments(scope.arguments, scope.defaults)[ident]
        else:
            expression_scope = scope.parent
            expression = dict(scope.defaults)[ident]

        scope_stack.append(expression_scope)
        output = expression()
        scope_stack.pop()

        return output
    if scope.self and scope.self is not scope:
        return _resolve_in_closure(ident, scope.self)
    return None


def _resolve(ident, scope):
    if ident in scope.items:
        scope_stack.append(_item_resolution_scope(scope))
        output = scope.items[ident]()
        scope_stack.pop()
        return output
    if ident == 'me':
        return scope
    if ident == 'self':
        return scope.self
    _closure_result = _resolve_in_closure(ident, scope)
    if _closure_result:
        return _closure_result
    if scope.parent:
        return _resolve(ident, scope.parent)
    return _create_failed(WRException('Key error: `%s`' % ident))


def resolve(ident):
    scope = scope_stack[-1]
    return _resolve(ident, scope)


def get(object, scope):
    value = object.raw
    if value in scope.items:
        return _new_with_self(scope.items[value](), scope)

    try:
        return _at_index(value, scope)
    except:  # all the bad things that happen when you do not_a_list[not_a_number] in python
        pass

    return _create_failed(WRException('Attribute error: `%s`' % value))


def _at_index(index, list):
    try:
        return list.raw[index]
    except IndexError as e:
        return _create_failed(WRException('Index out of range: %s' % index))


def slice(list, _from, _to=None):  # TODO consider renaming list to iterable
    _to = _to or len(list.raw)
    return create_native(list.raw[_from:_to])


def _new_with_arguments(prototype, arguments, arguments_scope):
    if prototype.arguments == arguments and prototype.arguments_scope == arguments_scope:
        return prototype
    output = Object(prototype=prototype)
    output.arguments = arguments
    output.arguments_scope = arguments_scope

    return output


def _new_with_self(prototype, self):
    output = Object(prototype=prototype)
    output.self = self

    return output


def _item_resolution_scope(scope):
    output = Object(prototype=scope.parent)
    output.defaults = scope.defaults
    output.arguments = scope.arguments

    return output


def _argument_resolution_scope(scope):
    return scope.parent


def _arguments(arguments, defaults):
    if not arguments:
        return {}

    output = dict([(defaults[0][0], arguments[0][1])] + arguments[1:])
    return output


def create_object(defaults=[], items={}, expression=None):
    output = create_native(items)

    output.defaults = defaults
    output.items.update(items)
    output.expression = expression
    output.parent = scope_stack[-1]
    output.arguments_scope = output.parent

    return output


def create_native(value):
    try:
        for e in value:
            if type(e.raw) is WRException:
                return _create_failed(WRException('Cannot create native list with failed objects'))
    except TypeError as e:
        pass  # non-iterables are ok
    except AttributeError as e:
        pass  # strings are iterable but should not fail

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
        'length': LV(lambda: create_object(
            expression=LV(lambda: _native_length(resolve('self')))
        )),
    }
    output.parent = scope_stack[0]
    output.arguments_scope = output.parent
    output.raw = value

    return output


def _create_failed(value):
    output = create_native(value)
    output.items = {
        'or': LV(lambda: create_object(
            defaults=[('other', None)],
            expression=LV(lambda: resolve('other'))
        )),
    }

    return output


def _native_length(o):
    return create_native(len(o.raw))


def _native_add(a, b):
    return create_native(a.raw + b.raw)


def evaluate_module(items={}, expression=None):
    # bootstrap scope_stack
    root = Object()
    scope_stack.append(root)

    module = create_object(items=items, expression=expression)

    return call(module, [])
