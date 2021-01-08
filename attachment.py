from __future__ import annotations
from css_parser import CSSOM
from html_parser import DOMNode
import re
from css_properties import *

INHERITABLE_PROPERTIES = [COLOR, BACKGROUND_COLOR, BORDER_COLOR, FONT_SIZE, FONT_STYLE, FONT_WEIGHT]


def parse_style(styles: dict):
    parsed_styles = {}

    def update_style(properties: [str], pattern: str, default_value: str):
        # For specified properties, function checks in values matches the pattern,
        # If value does not exist or does not match pattern, default value is used
        # to update value in parsed_styles otherwise corresponding value
        for prop in properties:
            value = styles.get(prop, default_value)
            if not re.match(pattern, value):
                value = default_value
            parsed_styles[prop] = value

    update_style([MARGIN_LEFT, MARGIN_RIGHT, MARGIN_TOP, MARGIN_BOTTOM,
                  PADDING_LEFT, PADDING_RIGHT, PADDING_TOP, PADDING_BOTTOM,
                  BORDER_LEFT, BORDER_RIGHT, BORDER_TOP, BORDER_BOTTOM],
                 r'^\d+(px|%)$', '0px')
    update_style([WIDTH, HEIGHT, LEFT, RIGHT, TOP, BOTTOM],
                 r'^(\d+(px|%)|auto)$', 'auto')

    update_style([COLOR, BORDER_COLOR], r'^(#[0-9a-f]{6}|inherit)$', 'inherit')
    update_style([BACKGROUND_COLOR], r'^(#[0-9a-f]{6}|transparent|inherit)$', 'inherit')

    update_style([FONT_SIZE], r'^(\d+px|inherit)$', 'inherit')
    update_style([FONT_WEIGHT], r'^(normal|bold|inherit)$', 'inherit')
    update_style([FONT_STYLE], r'^(normal|italic|inherit)$', 'inherit')

    update_style([DISPLAY], r'^(block|inline|none)$', 'none')
    update_style([POSITION], r'^(static|relative|absolute|fixed)$', 'static')

    return parsed_styles


def compute_style(node: DOMNode, cssom: CSSOM):
    # CSS Specificity and Cascade (partly)
    # apply universal styles
    node.styles.update(cssom.universal_rule.declarations)
    # override with tag styles
    if node.tag in cssom.tag_rules:
        node.styles.update(cssom.tag_rules[node.tag].declarations)
    # override with class styles
    for class_name in node.classes:
        if f'.{class_name}' in cssom.class_rules:
            node.styles.update(cssom.class_rules[f'.{class_name}'].declarations)
    # finally override with id styles
    if f'#{node.id}' in cssom.id_rules:
        node.styles.update(cssom.id_rules[f'#{node.id}'].declarations)

    # Filter out supported styles
    node.styles = parse_style(node.styles)

    # Override styles in case of HTML tag
    if node.tag == 'html':
        node.styles[POSITION] = 'relative'  # always a positioned element
        node.styles[DISPLAY] = 'block'  # always a block element
        # Root node cannot inherit properties
        # override values if `inherit`
        for prop, default_value in [(COLOR, '#000000'), (BORDER_COLOR, '#000000'), (BACKGROUND_COLOR, 'transparent'),
                                    (FONT_SIZE, '16px'), (FONT_WEIGHT, 'normal'), (FONT_STYLE, 'normal')]:
            if node.styles[prop] == 'inherit':
                node.styles[prop] = default_value

    # CSS Inheritance
    for prop in INHERITABLE_PROPERTIES:
        if node.styles[prop] == 'inherit':
            # If node's property is inherit, then picks up value from parent
            assert node.parent and node.parent.styles[prop] != 'inherit'
            node.styles[prop] = node.parent.styles[prop]


def attach_styles(dom: DOMNode, cssom: CSSOM):
    # Takes DOM and CSSOM and computes styles for each of the dom node.
    nodes = [dom]
    while nodes:  # Breadth First Traversal
        node = nodes.pop(0)
        compute_style(node, cssom)  # Compute parent's style before children
        for child_node in node.children:
            if isinstance(child_node, DOMNode):
                nodes.append(child_node)
