from __future__ import annotations
import re


class CSSRule:
    def __init__(self, selector):
        self.selector = selector
        self.declarations = {}

    def __setitem__(self, prop, value):
        self.declarations[prop] = value

    def __repr__(self):
        return f'CSSRule({self.selector!r})'

    def __str__(self):
        declarations = ' '.join(f'{prop}: {value};' for prop, value in self.declarations.items())
        return f'{self.selector} {{ {declarations} }}'


class CSSOM:  # CSS Object Model
    def __init__(self):
        self.universal_rule = CSSRule('*')
        self.tag_rules = {}
        self.class_rules = {}
        self.id_rules = {}

    def __getitem__(self, selector):
        # Returns corresponding CSS Rule for a given selector
        if re.match(r'^[*]$', selector):
            return self.universal_rule
        elif re.match(r'^[.][\w-]+$', selector):
            if selector not in self.class_rules:
                self.class_rules[selector] = CSSRule(selector)
            return self.class_rules[selector]
        elif re.match(r'^#[\w-]+$', selector):
            if selector not in self.id_rules:
                self.id_rules[selector] = CSSRule(selector)
            return self.id_rules[selector]
        elif re.match(r'^[\w-]+$', selector):
            if selector not in self.tag_rules:
                self.tag_rules[selector] = CSSRule(selector)
            return self.tag_rules[selector]
        raise NotImplementedError(f'Cannot handle selector {selector!r}')

    def __str__(self):
        return str(self.universal_rule) + '\n\n' \
               + '\n'.join(map(str, self.tag_rules.values())) + '\n\n' \
               + '\n'.join(map(str, self.class_rules.values())) + '\n\n' \
               + '\n'.join(map(str, self.id_rules.values()))


def parse(css, cssom=None):
    if cssom is None:
        cssom = CSSOM()

    comment = r'/[*].*?[*]/'
    css = re.sub(comment, '', css, flags=re.DOTALL)  # Remove comments - loses line info.
    selector = r'(?P<SELECTOR>[*]|[\w-]+|[.][\w-]+|[#][\w-]+)'
    declaration = r'(\s*(?P<PROPERTY>[\w-]+)\s*:\s*(?P<VALUE>#?\w+%?)\s*;)'
    rule = rf'\s*{selector}\s*{{(?P<DECLARATIONS>{declaration}+)\s*}}'
    token_specification = [
        ('RULE', rule),
        ('SPACE', r'\s+'),
        ('EXCEPTION', r'.+'),
    ]
    regex = '|'.join('(?P<%s>%s)' % pair for pair in token_specification)

    for m in re.finditer(regex, css):
        kind = m.lastgroup
        if kind == 'SPACE':
            continue
        elif kind == 'RULE':
            css_rule = cssom[m.group('SELECTOR').lower()]
            for n in re.finditer(declaration, m.group('DECLARATIONS')):
                css_rule[n.group('PROPERTY').lower()] = n.group('VALUE').lower()
        elif kind == 'EXCEPTION':
            print(f"Unexpected text `{m.group()!r}`")
    return cssom
