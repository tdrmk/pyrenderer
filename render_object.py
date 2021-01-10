from __future__ import annotations
from html_parser import DOMNode, TextNode
from typing import Union, List, Optional, TYPE_CHECKING
from css_properties import DISPLAY, POSITION, FONT_SIZE, FONT_WEIGHT, FONT_STYLE
from box_model import BoxModel

if TYPE_CHECKING:  # to prevent cycling dependency
    from text_layout import WordObject, RenderLines


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
    # Computed during the layout phase
    # `lines_object` is defined when the descendants are all inline/text objects
    lines_object: Optional[RenderLines]
    box_model: BoxModel

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
    words: List[WordObject]  # Computed in the layout phase

    def __init__(self, node: TextNode):
        self.node = node

    def __str__(self):
        return f'RenderText {self.node}'

    @property
    def font_size(self):
        font_size = self.parent.node.styles[FONT_SIZE]
        return int(font_size[:-2])

    @property
    def font_weight(self):
        return self.parent.node.styles[FONT_WEIGHT]

    @property
    def font_style(self):
        return self.parent.node.styles[FONT_STYLE]
