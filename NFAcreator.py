#coding=utf-8
import collections

#Here is the logic for transforming a parse tree. It's somewhat ugly, but
#pretty simple conceptually, just an in-order traversal of the tree creating
#NFA nodes according to the type of parse tree node (a Visitor-like solution
#might be better, but that would be a not-entirely-trivial architectural
#shift, so it will have to wait for now).
def walk_parse_tree(parseTree):
    #Group - combinations of or's
    if parseTree.non_terminal == "regex":
        return walk_parse_tree(parseTree.children[0])[0]
    elif parseTree.non_terminal == "group":
        #If there are children of children, then we need to construct NFA nodes
        if len(parseTree.children[1].children) != 0:
            return construct_or(walk_parse_tree(parseTree.children[0]),
                                walk_parse_tree(parseTree.children[1]))
        else:
            return walk_parse_tree(parseTree.children[0])
    elif parseTree.non_terminal == "group'":
        if len(parseTree.children) == 0:
            print("Unnecessarily walked on empty group'")
            return
        if len(parseTree.children[2].children) != 0:
            return construct_or(walk_parse_tree(parseTree.children[1]),
                                walk_parse_tree(parseTree.children[2]))
        elif len(parseTree.children) != 0:
            return walk_parse_tree(parseTree.children[1])
    #Concatgroup - concatenations
    elif parseTree.non_terminal == "concat_group":
        #If there are children of children, then we need to construct NFA nodes
        if len(parseTree.children[1].children) != 0:
            return construct_concat(walk_parse_tree(parseTree.children[0]),
                                    walk_parse_tree(parseTree.children[1]))
        else:
            return walk_parse_tree(parseTree.children[0])
    elif parseTree.non_terminal == "concat_group'":
        if len(parseTree.children) == 1:
            print("Unnecessarily walked on empty group'")
            return
        if len(parseTree.children[1].children) != 0:
            return construct_concat(walk_parse_tree(parseTree.children[0]),
                                walk_parse_tree(parseTree.children[1]))
        elif len(parseTree.children) != 0:
            return walk_parse_tree(parseTree.children[0])
    elif parseTree.non_terminal == "unary_group":
        #Change path based on second terminal
        if len(parseTree.children[1].children) == 0:
            return walk_parse_tree(parseTree.children[0])
        if parseTree.children[1].children[0].token == "*":
            return construct_star(walk_parse_tree(parseTree.children[0]))
        elif parseTree.children[1].children[0].token == "?":
            return construct_question(walk_parse_tree(parseTree.children[0]))
        elif parseTree.children[1].children[0].token == "+":
            return construct_plus(walk_parse_tree(parseTree.children[0]))
    elif parseTree.non_terminal == "char_group":
        if parseTree.children[0].token == "(":
            return walk_parse_tree(parseTree.children[1])
        elif parseTree.children[0].token == "[":
            #return construct_group(parseTree.children[1].terminal,
            #                       parseTree.children[2].)
            return construct_group_stub()
        else:
            return construct_char(parseTree.children[0].token)
    print("walk_parse_tree didn't match:", parseTree.non_terminal)
    return

class NFA:
    #if negated is true, then non-epsilon transitions
    def __init__(self, links=None, debug=False):
        if links is None:
            links = {}
        self.links = links
        self.num = id(self)
        #NFA.created += 1
        self.matching = False
        print_str = str(self.num) + ":"
        if debug:
            for link in self.links.values():
                for node in link:
                    print_str += " " + str(node.num) + ","
            print(print_str)
    
    def _add_link(self, char, transition_to, debug=False):
        if char not in self.links:
            self.links[char] = transition_to
        else:
            self.links[char].update(transition_to)
        if debug:
            print_str = str(self.create_num) + ":"
            for link in self.links[char]:
                print_str += " " + str(link.create_num) + ","
            print(print_str)

    ##TODO: Make this work for certain escaped characters. And anything else.
    def __str__(self):
        ret_str = str(self.num) + (" -- matching" if self.matching else "")
        for link in self.links.keys():
            if link == "":
                for node in self.links[link]:
                    ret_str += "\n\tε -> " + str(node.num)
            else:
                for node in self.links[link]:
                    ret_str += "\n\t"+link+" -> " + str(node.num)
        return ret_str + "\n"

    def __iter__(self):
        iter_list = []
        visited_nodes = {self}
        #Put objects in deque from left, remove them from right.
        node_queue = collections.deque([self])
        while len(node_queue) != 0:
            current_node = node_queue.pop()
            iter_list.append(current_node)
            for child in current_node.links.values():
                if not child.issubset(visited_nodes):
                    node_queue.extendleft(child - visited_nodes)
                    visited_nodes.update(child)
        for node in iter_list:
            yield node
    
    def __repr__(self):
        return str(self.num)

################################################################################
##---------------------------Construction Functions---------------------------##
################################################################################
def construct_or(p1, p2, debug=False):
    if debug: print("construct_or")
    (p1_start, p1_end) = p1
    (p2_start, p2_end) = p2
    p1_end.matching = False
    p2_end.matching = False
    newStartNFA = NFA({"":{p1_start, p2_start}})
    newEndNFA = NFA()
    newEndNFA.matching = True
    p1_end._add_link("", {newEndNFA})
    p2_end._add_link("", {newEndNFA})
    return (newStartNFA, newEndNFA)

def construct_concat(p1, p2, debug=False):
    if debug: print("construct_concat")
    (p1_start, p1_end) = p1
    (p2_start, p2_end) = p2
    p1_end.matching = False
    p1_end._add_link("", {p2_start})
    return (p1_start, p2_end)

def construct_star(p, debug=False):
    if debug: print("construct_star")
    (p_start, p_end) = p
    p_start._add_link("", {p_end})
    p_end._add_link("", {p_start})
    return (p_start, p_end)

def construct_star_old(p, debug=False):
    """deprecated"""
    if debug: print("construct_star")
    (p_start, p_end) = p
    p_end.matching = False
    newEndNFA = NFA()
    newEndNFA.matching = True
    newStartNFA = NFA({"":{p_start, newEndNFA}})
    p_end._add_link("", {newEndNFA})
    newEndNFA._add_link("", {newStartNFA})
    return (newStartNFA, newEndNFA)

def construct_question(p, debug=False):
    if debug: print("construct_question")
    (p_start, p_end) = p
    newStartNFA = NFA({"":{p_start, p_end}})
    return (newStartNFA, p_end)

def construct_plus(p, debug=False):
    if debug: print("construct_plus")
    (p_start, p_end) = p
    p_end._add_link("", {p_start})
    return (p_start, p_end)

def construct_char(char, debug=False):
    if debug: print("construct_char:", char)
    newEndNFA = NFA()
    newEndNFA.matching = True
    newStartNFA = NFA({char:{newEndNFA}})
    return (newStartNFA, newEndNFA)

#Eventually, I will become less full of fail and actually implement this
def construct_group_stub(debug=False):
    if debug: print("construct_group_stub")
    newEndNFA = NFA()
    newStartNFA = NFA({"": {newEndNFA}})
    newEndNFA.matching = True
    return (newStartNFA, newEndNFA)

## This function creates the group. Other functions will then add the links.
def construct_group(char_negate, debug=False):
    if debug: print("construct_group")
    newEndNFA = NFA()
    newEndNFA.matching = True
    return newEndNFA
    
    if not first_char < second_char:
        print("failiure: [", first_char, "+ ", second_char, "] is not",
              "a legal group", sep = "")
        stop()
    elif char_negate:
        newEndNFA = NFA()
        newStartNFA = NFA({[second_char, first_char]:[newEndNFA]})
    else:
        newEndNFA = NFA()
        newStartNFA = NFA({[first_char, second_char]:[newEndNFA]})
