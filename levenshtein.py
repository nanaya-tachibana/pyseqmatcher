import types
import collections

from dawg import Dawg


class SparseLevenshteinAutomaton:

    def __init__(self, string, max_distance,
                 insert_cost=None, delete_cost=None, replace_cost=None):
        self._str = string
        self._d = max_distance

        if insert_cost is None:
            insert_cost = dict()
        if isinstance(insert_cost, types.FunctionType):
            self._icost = insert_cost
        else:
            self._icost = lambda x: insert_cost.get(x, 1)

        if delete_cost is None:
            delete_cost = dict()
        if isinstance(delete_cost, types.FunctionType):
            self._dcost = delete_cost
        else:
            self._dcost = lambda x: delete_cost.get(x, 1)

        if replace_cost is None:
            replace_cost = dict()
        if isinstance(replace_cost, types.FunctionType):
            self._rcost = replace_cost
        else:
            self._rcost = \
                lambda x, y: replace_cost.get((x, y), 1) if x != y else 0

    def start_state(self):
        cost = 0
        state = collections.OrderedDict()
        state[-1] = cost
        for i, char in enumerate(self._str):
            cost += self._dcost(char)
            if cost <= self._d:
                state[i] = cost
            else:
                break
        return state

    def step(self, char, state=None):
        if state is None:
            state = self.start_state()

        new_state = collections.OrderedDict()
        if state:
            key = list(state.keys())[0]
            cost = state[key] + self._icost(char)
            if cost <= self._d:
                new_state[key] = cost

        for i, idx in enumerate(state.keys()):
            # replace
            if idx + 1 == len(self._str):
                continue
            cost = state[idx] + self._rcost(char, self._str[idx + 1])
            if idx in new_state:
                # delete
                cost = min(new_state[idx] + self._dcost(self._str[idx + 1]),
                           cost)

            if idx + 1 in state:
                # insert
                cost = min(state[idx + 1] + self._icost(char), cost)
            if cost <= self._d:
                new_state[idx + 1] = cost
        return new_state

    def can_match(self, state):
        return bool(state)

    def is_match(self, state):
        return state.get(len(self._str) - 1, self._d + 1) <= self._d


def levenshtein_distance(from_str, to_str,
                         max_cost=1, insert_cost=None,
                         delete_cost=None, replace_cost=None):
    """
    Return the levenshtein distance of transforming from_str to to_str.
    """
    lev_auto = SparseLevenshteinAutomaton(
        from_str, (len(from_str) + len(to_str)) * max_cost,
        insert_cost=insert_cost, delete_cost=delete_cost,
        replace_cost=replace_cost)
    state = lev_auto.start_state()
    for char in to_str:
        state = lev_auto.step(char, state)
    return state[len(from_str) - 1]


def levenshtein_search(graph, query_str, max_distance,
                       insert_cost=None, delete_cost=None, replace_cost=None):
    """
    Search candidates in graph.
    """
    lev_auto = SparseLevenshteinAutomaton(query_str, max_distance,
                                          insert_cost=insert_cost,
                                          delete_cost=delete_cost,
                                          replace_cost=replace_cost)
    state = lev_auto.start_state()
    stack = [('', graph.root, state)]
    searched = set()
    matched = set()
    while stack:
        word, node, state = stack.pop()
        if node._id in searched:
            continue
        searched.add(node._id)
        for char in node.edges:
            new_state = lev_auto.step(char, state)
            new_word = ''.join([word, char])
            child = node.edges[char]
            if lev_auto.is_match(new_state) and child.final:
                matched.add(new_word)
            if lev_auto.can_match(new_state):
                stack.append((new_word, child, new_state))
    return matched


if __name__ == '__main__':
    assert levenshtein_distance('abc', 'ab') == 1
    assert levenshtein_distance('bc', 'ab') == 2
    assert levenshtein_distance('adbc', 'bdac') == 2
    assert levenshtein_distance('', 'bdac') == 4
    assert levenshtein_distance('', '') == 0
    assert levenshtein_distance(
        'cd', 'abcd', insert_cost={c: 0.3 for c in 'abcd'}) == 0.6
    assert levenshtein_distance(
        'yudongqu', 'yuzhongqu',
        insert_cost={'h': 0.4, 'g': 0.4},
        delete_cost={'h': 0.4, 'g': 0.4},
        replace_cost={('d', 'z'): 0.4,
                      ('z', 'd'): 0.4,
                      ('b', 'd'): 0.4,
                      ('d', 'b'): 0.4}) == 0.8
    assert levenshtein_distance(
        'yuzhongqu', 'yudongqu',
        insert_cost={'h': 0.4, 'g': 0.4},
        delete_cost={'h': 0.4, 'g': 0.4},
        replace_cost={('d', 'z'): 0.4,
                      ('z', 'd'): 0.4,
                      ('b', 'd'): 0.4,
                      ('d', 'b'): 0.4}) == 0.8

    g = Dawg()
    for word in sorted(('yuzhongqu', 'wuzhongqu', 'dazhuxian',
                        'dazuqu', 'liangpingqu', 'baqiaoqu')):
        g.insert(word)
    g.finish()
    print(levenshtein_search(g, 'wudongqu', 0.8,
                             insert_cost={'h': 0.4, 'g': 0.4},
                             delete_cost={'h': 0.4, 'g': 0.4},
                             replace_cost={('d', 'z'): 0.4,
                                           ('z', 'd'): 0.4,
                                           ('b', 'd'): 0.4,
                                           ('d', 'b'): 0.4}))
