import re
from errors import *
from decorators import *

class GenericScanner (object):
    """Scans an input string and tokenizes it based on tokenizing rules
    defined in members of this class.
    
    Notes: There is a limitation in the Python regular expression library: 
    it doesn't use the POSIX semantics for the | alternation character.
    The side effect of this is that a combined regular expression, such
    as /in|init/ will never use its second alternative as a match. POSIX
    says the largest match should win, and that is the behavior used in
    Lex. This class does the right thing and finds the longest match 
    available. But in order to do this it has to check each match
    in turn. For this reason it may be less efficient than other 
    approaches.
    
    For matches that are the same length, the rule with the method
    name that comes first alphabetically will be chosen. The order of
    method declarations is ignored (because Python throws away this 
    information when it generates its __dict__).
    """
    def __init__(self):
        """Set up the scanner, and examine its defined methods to
        build a pattern table."""
        
        self.state = None
        self.patterns = {}

        # Check each valid name to see if it is a token declaration.
        for name in sorted(dir(self)):
            if name.startswith('t_') and name != 't_default':
                
                # Compile the regular expression for this rule.
                fn = getattr(self, name)
                regex, state = re.compile(fn.rule), fn.state
                
                # Add it to the pattern list for this state.
                self.patterns.setdefault(state, []).append((fn, regex))

        # Add the default pattern to each state
        entry = self.t_default, re.compile(self.t_default.rule)
        for entries in self.patterns.values():
            entries.append(entry)

    def tokenize(self, src_string):
        """Tokenizes the given string using the t_* rules defined in
        this instance."""
        
        pos = 0
        n = len(src_string)
        while pos < n:            
            assert self.state in self.patterns

            # Try each possible token regexp on this bit of string.
            longest = 0
            best = None
            for fn, regex in self.patterns[self.state]:
                m = regex.match(src_string, pos)
                if m is not None:
                    this_length = len(m.group(0))
                    if this_length > longest:
                        longest = this_length
                        best = fn, m
                        
            # Find the longest match.
            if best is None:
                raise SparkleInternalError(
                    "Lexical error at position %d." % pos
                    )
            fn, m = best
                    
            # Call the entry associated with the longest match
            fn(m.group(0), src_string, pos)

            # Start again from the end of the previous match
            if m.end() == pos:
                raise SparkleInternalError(
                    'Found empty match at %d.' % m.start()
                    )
            pos = m.end()

    @rule(r'( . | \n )+')
    def t_default(self, token, full_string, position):
        """The default rule that will be used (in all states) if no
        other rule matches. The default implementation raises an error.
        This can be overridden in a subclass to provide other 
        behaviour."""
        raise SparkleError("Found unmatched input at %d." % position)
