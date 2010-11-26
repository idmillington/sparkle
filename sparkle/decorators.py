from tokens import *
import functools

def rule(rule_definition, state=None, add_to_docstring=True):
    """A general purpose decorator-generator for methods that
    represent rules. This decorator adds two attributes to the
    method: the 'rule' attribute with the given rule strng in it
    and the 'state' attribute with the parsing state in which the
    rule is valid (or None for the default state).

    If add_to_docstring is True, it will also add the text
    representation of the rule to the end of the method's docstring.

    Usage:

    @rule(r"\n")
    def t_newline(self, token, string, position):
        ... act on this token ...
    """

    def _decorate(function):
        function.rule = rule_definition
        function.state = state
        if add_to_docstring:
            function.__doc__ = "%s\n\nRule: %s\n" % (
                function.__doc__, rule_definition
                )
        return function
    return _decorate

def generate_token(token_type):
    """
    Most often the scanner needs to return an appropriate token
    object. This parameterized decorator does that. The function it
    wraps should merely return the value to place in the token.
    """
    def _decorator(function):
        @functools.wraps(function)
        def _wraps(self, token, string, position):
            value = function(self, token, string, position)
            token = Token(token_type, value, position)
            self.tokens.append(token)
            return token
        return _wraps
    return _decorator
