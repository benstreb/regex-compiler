#This dictionary is nuts. Don't look too closely.
#Special symbols: eof, char
regex_dict = {
    "regex": {"(":["group"], "[":["group"], "char":["group"]},
    "group": {"(":["concat_group", "group'"], "[":["concat_group", "group'"], "char":["concat_group", "group'"]},
    "group'": { "eof":[], "|":["|", "concat_group", "group'"],")":[], "]":[]},
    "concat_group": {"(":["unary_group", "concat_group'"], "[":["unary_group", "concat_group'"], "char":["unary_group", "concat_group'"]},
    "concat_group'": {"eof":[], "|":[], "(":["unary_group", "concat_group'"], ")":[], "[":["unary_group", "concat_group'"], "char":["unary_group", "concat_group'"]},
    "unary_group": {"(":["char_group", "unary_op"], "[":["char_group", "unary_op"], "char":["char_group", "unary_op"]},
    "unary_op": {"*": ["*"], "?": ["?"], "+": ["+"], "(": [], "[": [], "char": [], ")": [], "|": [], "eof": []},
    "char_group": {"(":["(", "group", ")"], "[":["[", "char_negate", "char_group_inter", "]"], "char":["char"]},
    "char_group_inter": {"char":["char_type", "char_group_inter'"]},
    "char_group_inter": {"char":["char_type", "char_group_inter'"], "]":[]},
    "char_negate": {"char":[], "^":["^"]},
    "char_type": {"char":["char", "char_range"]},
    "char_range": {"char":[], "-":["-", "char"]}
}

char_exclusions = set(["(", ")", "[", "]", "|", "*", "?", "+", "^", "-"])

#This function makes sure that single characters get called "char" when they are
#searched for in the dictionary above.
def wrap(lexeme):
    if len(lexeme) == 1 and lexeme not in char_exclusions:
        return "char"
    else:
        return lexeme

class ParseTree:
    def __init__(self, non_terminal, token=None):
        self.non_terminal = non_terminal
        self.token = token
        self.parent = None
        self.children = []
    
    def add_child(self, child):
        self.children.append(child)
        child.parent = self
    
    def __str__(self):
        s = self._recurse_str(1)
        return s
    
    def _recurse_str(self, depth):
        if self.token:
            s = self.token
        else:
            s = self.non_terminal
        for child in self.children:
            s += "\n"+"  "*depth+child.recurse_str(depth+1)
        return s
    
    def get_regex(self):
        if self.token is not None:
            s = self.token
        else:
            s = ""
            for child in self.children:
                s += child.get_regex()
        return s

def parse_regex(token_stream, debug = False):
    next(token_stream)
    parse_tree = _parse_regex_recurse(token_stream, ParseTree("regex"), debug)
    try:
        next(token_stream)
    except StopIteration:
        #print("Parse successful.")
        pass
    else:
        raise SyntaxError("Malformed regex")
    return parse_tree

def _parse_regex_recurse(token_stream, non_terminal, debug):
    token_pair = token_stream.send(True)
    if debug:
        print(non_terminal.non_terminal, token_pair)
    try:
        for lexeme in regex_dict[non_terminal.non_terminal][wrap(token_pair[1])]:
            if lexeme in regex_dict:
                non_terminal.add_child(_parse_regex_recurse(token_stream, ParseTree(lexeme), debug))
            elif lexeme == "char":
                if token_pair[1] == "\\":
                    next(token_stream)
                    non_terminal.add_child(ParseTree("char", next(token_stream)[0]))
                else:
                    non_terminal.add_child(ParseTree("char", next(token_stream)[0]))
            else:
                non_terminal.add_child(ParseTree(lexeme, next(token_stream)[0]))
    except KeyError:
        if (debug):
            print("Failed to match lexeme", token_pair[1], "at non_terminal ", non_terminal.non_terminal)
        raise
    return non_terminal
            
            