class Token(object):
    """
    Holds a single token found from the scanning algorithm.
    """
    def __init__(self, token_type, value, position):
        self.token_type = token_type
        self.value = value
        self.position = position

    def __cmp__(self, token_type):
        """
        In the parser, the token gets compared to strings representing
        the different CFG elements. This comparison method allows us
        to compare tokens as if they were such strings.
        """
        return cmp(self.token_type, token_type)

    def __repr__(self):
        return "%s(%s, %s, %d)" % (
            self.__class__.__name__,
            repr(self.token_type),
            repr(self.value),
            self.position
            )

    def __hash__(self):
        return hash(self.token_type) ^ hash(self.value)

class AST(object):
    """
    A node in the generated AST.
    """
    __slots__ = ('expression')

    def __init__(self, *expression):
        self.expression = expression

    def __repr__(self):
        return "<%s %s>" % (
            self.__class__.__name__,
            ",".join([repr(item) for item in self.expression])
            )

    def walk(self, callback, *args, **kws):
        """
        Walks the AST calling the given callback once in depth-first
        order for each AST node in the tree.
        """
        callback(self, *args, **kws)
        for expression in self.expression:
            if hasattr(expression, 'walk'):
                expression.walk(callback, *args, **kws)
            elif not isinstance(expression, basestring):
                # Also try to go through sequences
                try:
                    for exp in expression:
                        if hasattr(exp, 'walk'):
                            exp.walk(callback, *args, **kws)
                except TypeError:
                    pass


    def get_complexity(self):
        """
        Returns a number indicating the complexity of this node.
        """
        total = 1
        for element in self.expression:
            if isinstance(element, AST):
                total += element.get_complexity()
        return total

    def __str__(self):
        return ""
