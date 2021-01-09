from __future__ import annotations
from html_parser import DOMNode, TextNode
from typing import Union, List, Optional
from css_properties import DISPLAY, POSITION


class RenderObject:
    node: Union[DOMNode, TextNode]
    parent: Optional[RenderChildren]


class RenderChildren(RenderObject):
    # RenderObject which have children
    children: List[RenderObject]

    def __init__(self):
        self.parent = None
        self.children = []

    def add_child(self, ro: RenderObject):
        ro.parent = self  # adopt the render object
        self.children.append(ro)

    def remove_child(self, ro: RenderObject):
        ro.parent = None  # abandon the render object
        self.children.remove(ro)

    def abandon_children(self):
        for child_ro in self.children:
            child_ro.parent = None  # abandon the render object
        children, self.children = self.children, []  # remove all children
        return children

    def insert_after(self, ro: RenderObject, sibling: RenderObject):
        # Inserts the `ro` node into children after `sibling`
        assert sibling in self.children
        ro.parent = self  # adopt the render object
        self.children.insert(self.children.index(sibling) + 1, ro)


class RenderBlock(RenderChildren):
    def __init__(self, node: DOMNode):
        RenderChildren.__init__(self)

        assert node.styles[DISPLAY] == 'block'
        self.node = node

    @property
    def position(self):
        return self.node.styles[POSITION]

    @property
    def is_positioned(self):
        return self.position in ['relative', 'fixed', 'absolute']

    def __str__(self):
        return f'RenderBlock[{self.position}] {self.node}'


class RenderInline(RenderChildren):
    def __init__(self, node: DOMNode):
        RenderChildren.__init__(self)

        assert node.styles[DISPLAY] == 'inline'
        self.node = node

    def __str__(self):
        return f'RenderInline {self.node}'


class RenderText(RenderObject):
    node: TextNode

    def __init__(self, node: TextNode):
        self.node = node

    def __str__(self):
        return f'RenderText {self.node}'


# These RenderObjects will be utilized during layout and paint phases
class RenderLines(RenderChildren):
    children: List[LineBox]


class LineBox(RenderChildren):
    children: List[InlineBox]


class InlineBox(RenderObject):
    pass
