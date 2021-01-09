from __future__ import annotations
from typing import Union, List
from utils import get_line_no, format_styles
import re


class Token:
    def __init__(self, kind, value, line, column):
        self.kind = kind
        self.value = value
        self.attributes = {}  # attribute keys, values are in lower case
        self.line = line
        self.column = column

    def __setitem__(self, key, value):
        self.attributes[key] = value

    def __repr__(self):
        return f'Token({self.kind}, {self.value})'

    def __str__(self):
        attributes = ' '.join(f'{key}="{value}"' for key, value in self.attributes.items())
        return f'TOKEN {self.kind} (line {self.line}, column {self.column}) {self.value!r} {attributes}'


def tokenize(html):
    # Converts HTML Page into tokens
    attribute = r'''[\w-]+=([\w-]+|'[\w\s-]+'|"[\w\s-]+")'''
    token_specification = [
        ('COMMENT', r'<!--.*?-->'),
        ('DOCTYPE', r'<!DOCTYPE.*?>'),
        ('START', rf'<[\w-]+(\s+{attribute})*\s*>'),
        ('CLOSING', rf'<[\w-]+(\s+{attribute})*\s*/>'),
        ('END', r'</[\w-]+\s*>'),
        ('SPACE', r'\s+'),
        ('TEXT', r'[^<]+'),
        ('EXCEPTION', r'.+'),
    ]
    regex = '|'.join('(?P<%s>%s)' % pair for pair in token_specification)
    for m in re.finditer(regex, html, flags=re.DOTALL | re.IGNORECASE):
        kind = m.lastgroup
        value = m.group()
        line, column = get_line_no(html, m.start())
        if kind in ['COMMENT', 'DOCTYPE', 'SPACE']:
            # Ignored, not part of DOM
            continue
        elif kind == 'TEXT':
            value = re.sub(r'\b(?=\w)', r' ', value)  # add spacing at word beginnings
            value = re.sub(r'\s+', r' ', value).strip()  # remove unnecessary spacing
            yield Token(kind, value, line, column)
        elif kind in ['START', 'CLOSING']:
            tag = re.match(rf'<(?P<TAG>[\w-]+)(\s+{attribute})*\s*/?>', value).group('TAG').lower()  # lower casing
            token = Token(kind, tag, line, column)
            for n in re.finditer(r'''(?P<PROPERTY>[\w-]+)=(?P<VALUE>[\w-]+|'[\w\s-]+'|"[\w\s-]+")''', value):
                token[n.group('PROPERTY').lower()] = n.group('VALUE').strip("\'\"").lower()  # lower casing
            yield token
        elif kind == 'END':
            tag = re.match(rf'</(?P<TAG>[\w-]+)\s*>', value).group('TAG').lower()  # lower casing
            yield Token(kind, tag, line, column)
        else:
            raise Exception(f'Unknown token {value!r} at line {line} column {column}.')


class DOMNode:
    children: List[Union[DOMNode, TextNode]]

    def __init__(self, tag, attributes, token):
        self.tag = tag
        self.attributes = attributes
        self.token = token
        self.parent = None  # will be set when added as a child
        self.children = []
        self.styles = {}  # will be populated in the attachment step

    @property
    def id(self):
        return self.attributes.get('id', '')

    @property
    def classes(self):
        return set(self.attributes.get('class', '').split())

    def add_child(self, node: Union[DOMNode, TextNode]):
        node.parent = self  # adopt the node
        self.children.append(node)

    def remove_child(self, node: Union[DOMNode, TextNode]):
        node.parent = None  # orphan the node
        self.children.remove(node)

    def __str__(self):
        return f'''DOMNode {self.tag} {self.id} {self.classes if self.classes else ''} {format_styles(self.styles)}'''


class TextNode:
    def __init__(self, text, token):
        self.text = text
        self.parent = None
        self.token = token

    def __str__(self):
        return f'TextNode {self.text!r}'


def parse(html):
    # Constructs DOM Tree from html text.
    # Supports some amount of error handling
    #   - Ignores some unexpected closing tags,
    #   - Can add closing tags when missing
    # However its not perfect as it does it blindly and does not understand the contexts
    stack = []  # contains DOM nodes only from START tokens
    root_node = None  # Will contain the document node
    for token in tokenize(html):
        if token.kind == 'TEXT':
            node = TextNode(token.value, token)
            if not stack:
                raise Exception(f'Unexpected text `{token.value}` '
                                f'at line {token.line} and column {token.column}')
            stack[-1].add_child(node)
        elif token.kind == 'CLOSING':
            node = DOMNode(token.value, token.attributes, token)
            if not stack:
                raise Exception(f'Unexpected self-closing tag `{token.value}` '
                                f'at line {token.line} and column {token.column}')
            stack[-1].add_child(node)
        elif token.kind == 'START':
            node = DOMNode(token.value, token.attributes, token)
            if stack:
                stack[-1].add_child(node)
            else:
                root_node = node  # The root level node
            stack.append(node)
        elif token.kind == 'END':
            if not stack:
                raise Exception(f'Unexpected end tag `{token.value}` '
                                f'at line {token.line} and column {token.column}')
            if stack[-1].tag != token.value:
                # If unexpected closing tag
                print(f'Unexpected tag `{token.value}` at line {token.line} and column {token.column}')
                temp_stack = stack[:]
                while temp_stack[-1].tag != token.value:
                    temp_stack.pop()
                    if not temp_stack:
                        print(f'Cannot find corresponding start tag for end tag `{token.value}` '
                              f'at line {token.line} and column {token.column}. Ignoring it.')
                        # Just ignore that closing tag
                        break
                else:
                    # If corresponding start tag found
                    while stack[-1].tag != token.value:
                        # Pop out values till it match
                        node = stack.pop()
                        print(f'Automatically closing start tag `{node.tag}` '
                              f'at line {node.token.line} and column {node.token.column}')
                    # Pop out the matching tag
                    stack.pop()
            else:
                # If matching closing tag
                stack.pop()  # Pop out the matching tag

            if not stack:
                # if stack is exhausted, then rest tokens are not useful
                break
    while stack:
        node = stack.pop()
        print(f'Automatically closing start tag `{node.tag}` '
              f'at line {node.token.line} and column {node.token.column}')

    assert root_node.tag == 'html'
    return root_node


def get_page_title(dom: DOMNode):
    assert dom.tag == 'html'
    for node in dom.children:
        if isinstance(node, DOMNode) and node.tag == 'head':
            for h_node in node.children:
                if isinstance(h_node, DOMNode) and h_node.tag == 'title':
                    for t_node in h_node.children:
                        if isinstance(t_node, TextNode):
                            return t_node.text
    return 'Default Title'
