import logging
logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger('src')
logger.setLevel(logging.DEBUG)


def _partial(f, a):
    def _lambda():
        return f(a)
    return _lambda


class LazyValue(object):
    def __init__(self, expression):
        self._expression = expression
        self._result = None

    def __call__(self):
        if not self._result:
            self._result = self._expression()
        return self._result


class Object(object):
    id_counter = 0

    def __init__(self, prototype=None):
        self._can_resolve_items = True

        if prototype is None:
            self.defaults = []
            self.items = {}
            self.expression = None
            self.arguments = []
            self.arguments_scope = None
            self.parent = None
            self.self = self
            self.raw = None
            self.stack_trace = []
        else:
            self.defaults = prototype.defaults
            self.items = prototype.items
            self.expression = LazyValue(prototype.expression._expression) if prototype.expression else None
            self.arguments = prototype.arguments
            self.arguments_scope = prototype.arguments_scope
            self.parent = prototype.parent
            self.self = prototype.self
            self.raw = prototype.raw
            self.stack_trace = list(prototype.stack_trace)

        self._id = Object.id_counter
        Object.id_counter += 1

    def __str__(self):
        return '''defaults %s
items %s
expression %s
arguments %s
parent %s
raw %s''' % (self.defaults, self.items, self.expression, self.arguments, self.parent is not None, self.raw)

    def __repr__(self):
        return str(self.raw)

class WRException(Exception):
    pass


# class FailedException(Exception):
#     def __init__(self, wr_exception):
#         self.raw = wr_exception
#
#
# def _check_failed(object):
#     if type(object.raw) is WRException:
#         raise FailedException(object)
