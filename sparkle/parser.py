from errors import *

class GenericParser(object):
    def __init__(self, start='root'):
        """
        Create the parse, so that its top level grammar element is given
        by the start parameter. This defaults to 'root'.
        """
        self.rules = {}
        self.rule2func = {}
        self.rule2name = {}

        # Find and add the rules
        for name in dir(self):
            if name.startswith("p_"):
                self._add_rule(getattr(self, name))

        self.start_rule = self._init_first_rule(start)
        self.rules_changed = 1

    def preprocess(self, rule, func):
        """
        Implement this method in subclasses to augment any rule that
        the parser contains. This allows you to centrally build an
        AST, for example.
        """
        return rule, func

    def parse(self, tokens):
        tree = {}
        tokens.append(self._EOF)
        states = { 0: [ (self.start_rule, 0, 0) ] }

        if self.rules_changed:
            self._make_first()

        for i in xrange(len(tokens)):
            states[i+1] = []

            if states[i] == []:
                break
            self._build_state(tokens[i], states, i, tree)

        if i < len(tokens)-1 or states[i+1] != [(self.start_rule, 2, 0)]:
            del tokens[-1]
            print tokens
            raise SparkleSyntaxError(
                "Syntax error at or near '%s'" % tokens[i-1],
                tokens[i-1].position
                )
        rv = self._build_tree(tokens, tree, ((self.start_rule, 2, 0), i+1))
        del tokens[-1]
        return rv

    # ........................................................................
    # Internal data and functions

    _START = 'START'
    _EOF = 'EOF'

    def _add_rule(self, func):
        """
        Adds the given rule function to the database of rules. The
        rule function should have a .rule property containing the
        grammar production.
        """
        rules = func.rule.split()

        index = []
        for i in range(len(rules)):
            if rules[i] == '::=':
                index.append(i-1)
        index.append(len(rules))

        for i in range(len(index)-1):
            lhs = rules[index[i]]
            rhs = rules[index[i]+2:index[i+1]]
            rule = (lhs, tuple(rhs))

            rule, processed_func = self.preprocess(rule, func)

            if self.rules.has_key(lhs):
                self.rules[lhs].append(rule)
            else:
                self.rules[lhs] = [rule]
            self.rule2func[rule] = processed_func
            self.rule2name[rule] = func.__name__[2:]
        self.rules_changed = 1

    def _init_first_rule(self, start):
        #
        #  Tempting though it is, this isn't made into a call
        #  to self.add_rule() because the start rule shouldn't
        #  be subject to preprocessing.
        #
        start_rule = (self._START, ( start, self._EOF ))
        self.rule2func[start_rule] = lambda args: args[0]
        self.rules[self._START] = [ start_rule ]
        self.rule2name[start_rule] = ''
        return start_rule

    def _make_first(self):
        union = {}
        self.first = {}

        for rulelist in self.rules.values():
            for lhs, rhs in rulelist:
                if not self.first.has_key(lhs):
                    self.first[lhs] = {}

                if len(rhs) == 0:
                    self.first[lhs][None] = 1
                    continue

                sym = rhs[0]
                if not self.rules.has_key(sym):
                    self.first[lhs][sym] = 1
                else:
                    union[(sym, lhs)] = 1

        changes = 1
        while changes:
            changes = 0
            for src, dest in union.keys():
                destlen = len(self.first[dest])
                self.first[dest].update(self.first[src])
                if len(self.first[dest]) != destlen:
                    changes = 1

    #
    #  An Earley parser, as per J. Earley, "An Efficient Context-Free
    #  Parsing Algorithm", CACM 13(2), pp. 94-102.  Also J. C. Earley,
    #  "An Efficient Context-Free Parsing Algorithm", Ph.D. thesis,
    #  Carnegie-Mellon University, August 1968, p. 27.
    #

    def _type_string(self, token):
        return None

    def _build_state(self, token, states, i, tree):
        needs_completion = {}
        state = states[i]
        predicted = {}

        for item in state:
            rule, pos, parent = item
            lhs, rhs = rule

            #
            #  A -> a . (completer)
            #
            if pos == len(rhs):
                if len(rhs) == 0:
                    needs_completion[lhs] = (item, i)

                for pitem in states[parent]:
                    if pitem is item:
                        break

                    prule, ppos, pparent = pitem
                    plhs, prhs = prule

                    if prhs[ppos:ppos+1] == (lhs,):
                        new = (prule,
                               ppos+1,
                               pparent)
                        if new not in state:
                            state.append(new)
                            tree[(new, i)] = [(item, i)]
                        else:
                            tree[(new, i)].append((item, i))
                continue

            next_symbol = rhs[pos]

            #
            #  A -> a . B (predictor)
            #
            if self.rules.has_key(next_symbol):
                #
                #  Work on completer step some more; for rules
                #  with empty RHS, the "parent state" is the
                #  current state we're adding Earley items to,
                #  so the Earley items the completer step needs
                #  may not all be present when it runs.
                #
                if needs_completion.has_key(next_symbol):
                    new = (rule, pos+1, parent)
                    olditem_i = needs_completion[next_symbol]
                    if new not in state:
                        state.append(new)
                        tree[(new, i)] = [olditem_i]
                    else:
                        tree[(new, i)].append(olditem_i)

                #
                #  Has this been predicted already?
                #
                if predicted.has_key(next_symbol):
                    continue
                predicted[next_symbol] = 1

                ttype = token is not self._EOF and \
                    self._type_string(token) or \
                    None
                if ttype is not None:
                    #
                    #  Even smarter predictor, when the
                    #  token's type is known.  The code is
                    #  grungy, but runs pretty fast.  Three
                    #  cases are looked for: rules with
                    #  empty RHS; first symbol on RHS is a
                    #  terminal; first symbol on RHS is a
                    #  nonterminal (and isn't nullable).
                    #
                    for prule in self.rules[next_symbol]:
                        new = (prule, 0, i)
                        prhs = prule[1]
                        if len(prhs) == 0:
                            state.append(new)
                            continue
                        prhs0 = prhs[0]
                        if not self.rules.has_key(prhs0):
                            if prhs0 != ttype:
                                continue
                            else:
                                state.append(new)
                                continue
                        first = self.first[prhs0]
                        if not first.has_key(None) and \
                           not first.has_key(ttype):
                            continue
                        state.append(new)
                    continue

                for prule in self.rules[next_symbol]:
                    #
                    #  Smarter predictor, as per Grune &
                    #  Jacobs' _Parsing Techniques_.  Not
                    #  as good as FIRST sets though.
                    #
                    prhs = prule[1]
                    if len(prhs) > 0 and \
                       not self.rules.has_key(prhs[0]) and \
                       token != prhs[0]:
                        continue
                    state.append((prule, 0, i))

            #
            #  A -> a . c (scanner)
            #
            elif token == next_symbol:
                #assert new not in states[i+1]
                states[i+1].append((rule, pos+1, parent))

    def _build_tree(self, tokens, tree, root):
        stack = []
        self._build_tree_recursive(stack, tokens, -1, tree, root)
        return stack[0]

    def _build_tree_recursive(self, stack, tokens, tokpos, tree, root):
        (rule, pos, parent), state = root

        while pos > 0:
            want = ((rule, pos, parent), state)
            if not tree.has_key(want):
                #
                #  Since pos > 0, it didn't come from closure,
                #  and if it isn't in tree[], then there must
                #  be a terminal symbol to the left of the dot.
                #  (It must be from a "scanner" step.)
                #
                pos = pos - 1
                state = state - 1
                stack.insert(0, tokens[tokpos])
                tokpos = tokpos - 1
            else:
                #
                #  There's a NT to the left of the dot.
                #  Follow the tree pointer recursively (>1
                #  tree pointers from it indicates ambiguity).
                #  Since the item must have come about from a
                #  "completer" step, the state where the item
                #  came from must be the parent state of the
                #  item the tree pointer points to.
                #
                children = tree[want]
                if len(children) > 1:
                    child = self._ambiguity(children)
                else:
                    child = children[0]

                tokpos = self._build_tree_recursive(
                    stack, tokens, tokpos, tree, child
                    )
                pos = pos - 1
                (crule, cpos, cparent), cstate = child
                state = cparent

        lhs, rhs = rule
        result = self.rule2func[rule](stack[:len(rhs)])
        stack[:len(rhs)] = [result]
        return tokpos

    def _ambiguity(self, children):
        #
        #  XXX - problem here and in collect_rules() if the same
        #     rule appears in >1 method.  But in that case the
        #     user probably gets what they deserve :-)  Also
        #     undefined results if rules causing the ambiguity
        #     appear in the same method.
        #
        sortlist = []
        name2index = {}
        for i in range(len(children)):
            ((rule, pos, parent), index) = children[i]
            lhs, rhs = rule
            name = self.rule2name[rule]
            sortlist.append((len(rhs), name))
            name2index[name] = i
        sortlist.sort()
        list = map(lambda (a,b): b, sortlist)
        return children[name2index[self._resolve(list)]]

    def _resolve(self, list):
        #
        #  Resolve ambiguity in favor of the shortest RHS.
        #  Since we walk the tree from the top down, this
        #  should effectively resolve in favor of a "shift".
        #
        return list[0]



# This code is based on Spark by John Aycock.Original copyright
# message below:

#  Copyright (c) 1998-2000 John Aycock
#
#  Permission is hereby granted, free of charge, to any person obtaining
#  a copy of this software and associated documentation files (the
#  "Software"), to deal in the Software without restriction, including
#  without limitation the rights to use, copy, modify, merge, publish,
#  distribute, sublicense, and/or sell copies of the Software, and to
#  permit persons to whom the Software is furnished to do so, subject to
#  the following conditions:
#
#  The above copyright notice and this permission notice shall be
#  included in all copies or substantial portions of the Software.
#
#  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
#  EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
#  MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
#  IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
#  CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
#  TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
#  SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
