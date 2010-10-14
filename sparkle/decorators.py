def rule(rule_definition, state=None, add_to_docstring=True):
    """A general purpose decorator-generator for methods that
    represent rules. This decorator adds two attributes to the 
    method: the 'rule' attribute with the given rule string in it 
    and the 'state' attribute with the parsing state in which the 
    rule is valid (or None for the default state).
    
    If add_to_docstring is True, it will also add the text 
    representation of the rule to the end of the method's docstring.

    Usage:

    @rule(r"\n")
    def t_newline(self, token, string, position): 
        ... act on this token ...
    """

    def _decorate(fn):
        fn.rule = rule_definition
        fn.state = state
        if add_to_docstring:
            fn.__doc__ = "%s\n\nRule: %s\n" % (fn.__doc__, rule_definition)
        return fn

    return _decorate
