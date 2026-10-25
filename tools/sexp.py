"""Minimal KiCad s-expression parser/serializer.

parse() returns nested Python lists. Quoted strings become Str (a str subclass)
so dump() can re-quote exactly what was quoted in the source; bare tokens stay
plain str and are written back bare."""
import re

class Str(str):
    """A token that was quoted in the source file."""

_TOK = re.compile(r'"(?:[^"\\]|\\.)*"|\(|\)|[^\s()"]+')

def parse(text):
    stack = [[]]
    for m in _TOK.finditer(text):
        t = m.group(0)
        if t == '(':
            stack.append([])
        elif t == ')':
            node = stack.pop()
            stack[-1].append(node)
        elif t.startswith('"'):
            stack[-1].append(Str(t[1:-1].replace('\\"', '"').replace('\\\\', '\\')))
        else:
            stack[-1].append(t)
    return stack[0]

def find(node, key):
    return [n for n in node if isinstance(n, list) and n and n[0] == key]

def find1(node, key):
    r = find(node, key)
    return r[0] if r else None

def q(x):
    if isinstance(x, Str):
        return '"' + x.replace('\\', '\\\\').replace('"', '\\"') + '"'
    if isinstance(x, (int, float)):
        return repr(x)
    return x

def dump(node, ind=0):
    if not isinstance(node, list):
        return q(node)
    if all(not isinstance(x, list) for x in node):
        return '(' + ' '.join(q(x) for x in node) + ')'
    s = '(' + ' '.join(q(x) for x in node if not isinstance(x, list))
    for x in node:
        if isinstance(x, list):
            s += '\n' + '\t' * (ind + 1) + dump(x, ind + 1)
    return s + '\n' + '\t' * ind + ')'
