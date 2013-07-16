#We use a manually generated LL(1) parser, and this is the transition table in
#dict form. It maps from start state to {lookahead token to production}.
#Special symbols: eof, char
#Note also the primes (')
regex_dict = {
    "regex": {"(":["group"], "[":["group"], "char":["group"]},
    "group": {"(":["concat_group", "group'"],
              "[":["concat_group", "group'"],
              "char":["concat_group", "group'"]},
    "group'": {"eof":[], "|":["|", "concat_group", "group'"],")":[], "]":[]},
    "concat_group": {"(":["unary_group", "concat_group'"],
                     "[":["unary_group", "concat_group'"],
                     "char":["unary_group", "concat_group'"]},
    "concat_group'": {"eof":[], "|":[], "(":["unary_group", "concat_group'"],
                      ")":[], "[":["unary_group", "concat_group'"],
                       "char":["unary_group", "concat_group'"]},
    "unary_group": {"(":["char_group", "unary_op"],
                    "[":["char_group", "unary_op"],
                    "char":["char_group", "unary_op"]},
    "unary_op": {"*": ["*"], "?": ["?"], "+": ["+"], "(": [], "[": [],
                 "char": [], ")": [], "|": [], "eof": []},
    "char_group": {"(":["(", "group", ")"],
                   "[":["[", "char_negate", "char_group_inter", "]"],
                   "char":["char"]},
    "char_group_inter": {"char":["char_type", "char_group_inter'"]},
    "char_group_inter'": {"char":["char_type", "char_group_inter'"], "]":[]},
    "char_negate": {"char":[], "^":["^"]},
    "char_type": {"char":["char", "char_range"]},
    "char_range": {"char":[], "-":["-", "char"]},
}

#If it's not a terminal, it's a character. This breaks on combining characters,
#and possibly other parts of unicode, but that's a problem for some other time.
non_terminals = set(regex_dict)
terminals = set(["(", ")", "[", "]", "|", "*", "?", "+", "^", "-"])
def wrap(lexeme):
    if len(lexeme) == 1 and lexeme not in terminals:
        return "char"
    else:
        return lexeme

#This class represents a parse tree.
#It's just a tree with non_terminal or token as payloads.
class ParseTree:
    def __init__(self, non_terminal, token=None):
        self.non_terminal = non_terminal
        self.token = token
        self.children = []
    
    def _add_child(self, child):
        self.children.append(child)
    
    def __str__(self):
        s = self._recurse_str(1)
        return s
    
    def _recurse_str(self, depth):
        if self.token:
            s = self.token
        else:
            s = self.non_terminal
        for child in self.children:
            s += "\n"+"  "*depth+child._recurse_str(depth+1)
        return s
    
    def get_regex(self):
        if self.token is not None:
            s = self.token
        else:
            s = ""
            for child in self.children:
                s += child.get_regex()
        return s

#This is sent to the token stream when a token should be consumed.
CONSUME = object()
#Creates a parse tree from a given token stream. The token stream should be a
#generator where next returns the same token repeatedly until CONSUME is sent
#to it, at which point the stream should be advanced.
def parse_regex(token_stream, debug = False):
    #next(token_stream)
    parse_tree = _parse_regex_recurse(token_stream, ParseTree("regex"), debug)
    try:
        token_stream.send(CONSUME)
    except StopIteration:
        #print("Parse successful.")
        pass
    else:
        raise SyntaxError("Malformed regex")
    return parse_tree

#The algorithm to construct the parse tree is pretty simple:
#Start with "regex" as the non-terminal,
#Look up the next token in the transition table to get the new non-terminal.
#Add the new non-terminal+token (if applicable) to the transition table.
#Recurse, unless the non-terminal is actually a terminal.
def _parse_regex_recurse(token_stream, non_terminal, debug):
    next_token = next(token_stream)
    if debug:
        print(non_terminal.non_terminal, next_token)
    try:
        for lexeme in regex_dict[non_terminal.non_terminal][
                                                wrap(next_token)]:
            if lexeme in non_terminals:
                non_terminal._add_child(_parse_regex_recurse(
                                    token_stream, ParseTree(lexeme), debug))
            else:
                if next(token_stream) == "\\":
                    token_stream.send(CONSUME)
                non_terminal._add_child(ParseTree(lexeme, next(token_stream)))
                token_stream.send(CONSUME)
    except KeyError:
        if (debug):
            print("Failed to match lexeme", next(token_stream),
                  "at non_terminal", non_terminal.non_terminal)
        raise
    return non_terminal
