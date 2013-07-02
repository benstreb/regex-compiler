#coding=utf-8
from NFAcreator import NFA
import collections
from functools import reduce

#Takes in an NFA node or a set of NFA nodes and returns a set of NFA nodes
def _e_closure(NFA_nodes):
    visited_nodes = {NFA_nodes} if type(NFA_nodes) == NFA else set(NFA_nodes)
    #Put objects in deque from left, remove them from right.
    node_queue = collections.deque(visited_nodes)
    while len(node_queue) != 0:
        current_node = node_queue.pop()
        for child in (current_node.links[link] for link
                      in current_node.links if link == ""):
            if not child.issubset(visited_nodes):
                node_queue.extendleft(child - visited_nodes)
                visited_nodes.update(child)
    return visited_nodes

def _move(NFA_nodes, char):
    ret_set = set()
    for node in NFA_nodes:
        if char in node.links:
            ret_set.update(node.links[char])
    return ret_set

class DFA:
    created = 1
    DFAs = dict()
    def __new__(cls, NFA_nodes, links=None, debug=False):
        #print("Hi", DFA.created)
        if links is None:
            links = {}
        name = NFA_set_name(NFA_nodes)
        if name in cls.DFAs:
            return cls.DFAs[name]
        else:
            matching = any((NFA_node.matching for NFA_node in NFA_nodes))
            #new_DFA = super(DFA, cls).__new__(cls)
            new_DFA = super().__new__(cls)
            new_DFA.__define(name, matching, links, debug)
            cls.DFAs[name] = new_DFA
            return new_DFA
    
    @classmethod
    def reset(cls):
        cls.DFAs = {}
        cls.created = 1
    
    def __define(self, name, matching, links, debug):
        self.name = name
        self.links = links
        self.num = 0
        self.created = DFA.created
        DFA.created += 1
        self.matching = matching
        print_str = str(self.created) + ":"
        if debug:
            for link in self.links.values():
                for node in link:
                    print_str += " " + str(node.created) + ","
            print(print_str)
        self.DFAs = type(self).DFAs
    
    def add_link(self, char, transition_to, debug=False):
        #print(self.created, char, transition_to.created)
        if char not in self.links:
            self.links[char] = transition_to
        else:
            if transition_to == self.links[char]:
                return
            raise TypeError("DFAs cannot have more than one transition for the"+
                            " same character")
        if debug:
            print_str = str(self.created) + ":"
            for link in self.links[char]:
                print_str += " " + str(link.created) + ","
            print(print_str)

    def DFA_str(self):
        ret_str = ""
        for node in self:
            ret_str += str(node)
        return ret_str
    
    ##TODO: Make this work for certain escaped characters. And anything else.
    def __str__(self):
        ret_str = str(self.num) + (" -- matching" if self.matching else "")
        for link in self.links.keys():
            if link == "":
                ret_str += "\n\tε -> " + str(self.links[link].num)
            else:
                ret_str += "\n\t"+link+" -> " + str(self.links[link].num)
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
                if child not in visited_nodes:
                    node_queue.appendleft(child)
                    visited_nodes.add(child)
        for node in iter_list:
            yield node
    
    def __eq__(self, other):
        return self.name == other.name
    
    def __hash__(self):
        return hash(self.name)
    
    def __repr__(self):
        return "({"+ "".join("'"+link+"':'"+to.name+"'," for link, to in self.links.items()) + "}, "+str(self.matching)+")"

def add_nums(dfa):
    current_num = 0
    for node in dfa:
        current_num += 1
        node.num = current_num

def NFA_set_name(NFA_set):
    return reduce((lambda s,n:s+str(n.num)+" "), NFA_set, "")

def to_DFA(nfa):
    DFA_set = set()
    NFA_set = _e_closure(nfa)
    DFA_node = DFA(NFA_set)
    DFA_queue = collections.deque()
    DFA_set.add(DFA_node)
    DFA_queue.appendleft((DFA_node, NFA_set))
    char_set = _e_closure(DFA_node)
    ret_DFA = DFA_node
    [char_set.update(set(node.links.keys())) for node in nfa]
    if "" in char_set:
        char_set.remove("")
    while len(DFA_queue) > 0:
        (DFA_node, NFA_set) = DFA_queue.pop()
        for char in char_set:
            new_NFA_set = _move(NFA_set, char)
            new_NFA_set.update(_e_closure(new_NFA_set))
            if new_NFA_set != set():
                new_DFA_node = DFA(new_NFA_set)
                DFA_node.add_link(char, new_DFA_node)
                if new_DFA_node not in DFA_set:
                    DFA_set.add(DFA_node)
                    DFA_queue.appendleft((new_DFA_node, new_NFA_set))
    DFA.reset()
    return ret_DFA
    
    