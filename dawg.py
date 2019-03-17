#!/usr/bin/python3
# By Steve Hanov, 2011. Released to the public domain.
# Please see http://stevehanov.ca/blog/index.php?id=115 for the accompanying article.
#
# Based on Daciuk, Jan, et al. "Incremental construction of minimal acyclic finite-state automata."
# Computational linguistics 26.1 (2000): 3-16.
#
# Kowaltowski, T.; CL. Lucchesi (1993), "Applications of finite automata representing large vocabularies",
# Software-Practice and Experience 1993


# This class represents a node in the directed acyclic word graph (DAWG). It
# has a list of edges to other nodes. It has functions for testing whether it
# is equivalent to another node. Nodes are equivalent if they have identical
# edges, and each identical edge leads to identical states. The __hash__ and
# __eq__ functions allow it to be used as a key in a python dictionary.
class DawgNode:
    _next_id = 0

    def __init__(self):
        self._id = DawgNode._next_id
        DawgNode._next_id += 1
        self.final = False
        self.edges = {}
        # Number of end nodes reachable from this one.
        self._count = 0

    def __str__(self):
        arr = []
        if self.final:
            arr.append('1')
        else:
            arr.append('0')

        for label in self.edges:
            child = self.edges[label]
            arr.append(label)
            arr.append(str(child._id))

        return '_'.join(arr)

    def __hash__(self):
        return self.__str__().__hash__()

    def __eq__(self, other):
        return self.__str__() == other.__str__()

    @property
    def count(self):
        # if a count is already assigned, return it
        if self._count:
            return self._count

        # count the number of final nodes that are reachable from this one.
        # including self
        count = 0
        if self.final:
            count += 1
        for label in self.edges:
            child = self.edges[label]
            count += child.count

        self._count = count
        return count


class Dawg:
    def __init__(self):
        self._previous_word = ''
        self._root = DawgNode()
        # Here is a list of nodes that have not been checked for duplication.
        self._unchecked_nodes = []
        # Here is a list of unique nodes that have been checked for
        # duplication.
        self._minimized_nodes = {}

    def insert(self, word):
        if word <= self._previous_word:
            raise Exception("Error: Words must be inserted in alphabetical " +
                            "order.")
        # find common prefix between word and previous word
        common_prefix = 0
        for i in range(min(len(word), len(self._previous_word))):
            if word[i] != self._previous_word[i]:
                break
            common_prefix += 1

        # Check the uncheckedNodes for redundant nodes, proceeding from last
        # one down to the common prefix size. Then truncate the list at that
        # point.
        self._minimize(common_prefix)
        # self.data.append(data)
        # add the suffix, starting from the correct node mid-way through the
        # graph
        if len(self._unchecked_nodes) == 0:
            node = self._root
        else:
            node = self._unchecked_nodes[-1][2]

        for char in word[common_prefix:]:
            next_node = DawgNode()
            node.edges[char] = next_node
            self._unchecked_nodes.append((node, char, next_node))
            node = next_node

        node.final = True
        self._previous_word = word

    def finish(self):
        # minimize all uncheckedNodes
        self._minimize(0)
        # go through entire structure and assign the counts to each node.
        self._root.count

    def _minimize(self, down_to):
        # proceed from the leaf up to a certain point
        for i in range(len(self._unchecked_nodes) - 1, down_to - 1, -1):
            (parent, char, child) = self._unchecked_nodes[i]
            if child in self._minimized_nodes:
                # replace the child with the previously encountered one
                parent.edges[char] = self._minimized_nodes[child]
            else:
                # add the state to the minimized nodes.
                self._minimized_nodes[child] = child
            self._unchecked_nodes.pop()

    # def lookup(self, word):
    #     node = self.root
    #     skipped = 0  # keep track of number of final nodes that we skipped
    #     for char in word:
    #         if char not in node.edges:
    #             return None
    #         for label, child in sorted(node.edges.items()):
    #             if label == char:
    #                 if node.final:
    #                     skipped += 1
    #                 node = child
    #                 break
    #             skipped += child.count
    #     if node.final:
    #         return self.data[skipped]
    @property
    def root(self):
        return self._root

    @property
    def node_count(self):
        return len(self._minimized_nodes) + 1

    @property
    def edge_count(self):
        count = len(self._root.edges)
        for node in self._minimized_nodes:
            count += len(node.edges)
        return count

    def display(self):
        stack = [self._root]
        done = set()
        while stack:
            node = stack.pop()
            if node._id in done:
                continue
            done.add(node._id)
            print('{}: ({})'.format(node._id, node))
            for label in node.edges:
                child = node.edges[label]
                print('    {} goto {}'.format(label, child._id))
                stack.append(child)
