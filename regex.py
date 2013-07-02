import regexparser
import NFAcreator
import NFAtoDFA

DFA_cache = {}
def matches(regex, string):
    #print(regex)
    #print(string)
    if regex in DFA_cache:
        DFA = DFA_cache[regex]
    else:
        DFA = create_DFA(create_NFA(parse(regex)))
        DFA_cache[regex] = DFA
        #print(DFA.DFA_str())
    try:
        DFA_node = DFA
        for ch in string:
            DFA_node = DFA_node.links[ch]
    except KeyError:
        #print(regex, "doesn't match", string)
        return False
    else:
        if DFA_node.matching:
            #print(regex, "matches", string)
            return True
        else:
            #print(regex, "doesn't match", string)
            return False
    

def tokenize(regex):
    repeat = True
    index = 0
    strLen = len(regex)
    token = None
    next_token = None
    while index < strLen:
        if regex[index].isspace():
            pass
        else:
            token = next_token
            next_token = regex[index]
            repeat = yield (token, next_token)
            while repeat is not None:
                repeat = yield (token, next_token)
        index += 1
    token = next_token
    next_token = "eof"
    repeat = yield (token, next_token)
    while repeat is not None:
        repeat = yield (token, next_token)

def parse(regex, debug = False):
    return regexparser.parse_regex(tokenize(regex), debug)
    
    
def test_parse(regex):
    retry = False
    try:
        print(parse(regex).get_regex())
        print()
        print(parse(regex))
        print("\n")
    except:
        retry = True
    if retry:
        print(parse(regex, True).get_regex())

def create_NFA(parseTree):
    NFA = NFAcreator.walk_parse_tree(parseTree)
    NFAcreator.add_nums(NFA)
    return NFA

def run_test(regex, should_match, should_not_match):
    print("Testing \"", regex, '"', sep="")
    #NFAcreator.NFA.create = 1
    generate(regex, "regextest.py")
    import imp, regextest
    imp.reload(regextest)

    for match in should_match:
        if not regextest.matches(match):
            print('/!\\ Failed to match "', match, '" /!\\', sep="")
    for not_match in should_not_match:
        if regextest.matches(not_match):
            print('/!\\ Matched "', not_match, '" incorrectly /!\\', sep="")
    try:
        input()
    except EOFError:
        pass

#TODO: Far off: Add special escape characters.
def run_tests():
    run_test("a",
        ("a"),
        ("b", "aa"))
    run_test("a*b*",
        ("", "a", "b", "ab", "aaabb"),
        ("c", "aaabbc"))
    run_test("a|b",
        ("a", "b"),
        ("", "ab", "c"))
    #run_test("[a-z]")
    #run_test("[^a-z]")
    run_test("abc|a?",
        ("", "abc", "a"),
        ("abca", "aa", "d"))
    run_test(r"\+",
        ("+"),
        ("\\", r"\+"))
    run_test("a(a|b)c*",
        ("aa", "abc", "aacccc"),
        ("ac", "aacaac", "abcbc"))
    run_test("a*b|c+",
        ("b", "aab", "ccc"),
        ("aaa", "bc", "accc"))
    run_test("a(b|c)*a?",
        ("a", "aa", "abccb", "abca"),
        ("abaca", "bca", "abaa"))
    pathological_test(25)
    
def pathological_test(n):
    run_test("a?"*n+"a"*n,
        ("a"*n,),
        ())

def create_DFA(NFA):
    DFA = NFAtoDFA.to_DFA(NFA)
    NFAtoDFA.add_nums(DFA)
    return DFA

def generate(regex, file_name):
    with open("regexoutput.py.template", 'r') as template, open(file_name, 'w') as instantiation:
        template = "".join(line for line in template)
        DFA = create_DFA(create_NFA(parse(regex)))
        print(template.format(DFA), file=instantiation)
        NFAtoDFA.DFA.reset()

# regex = input("Enter regex: ")
# while regex != "":
#     string = input("Enter string: ")
#     matches(regex, string)
#     if input("Enter 'y' to use the same regex: ") != 'y':
#         regex = input("Enter regex: ")
    

#import time
#for i in range(1, 30):
#    start_time = time.clock()
#    pathological_test(i)
#    print("Took:", time.clock()-start_time, "seconds")
run_tests()
