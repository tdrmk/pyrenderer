from __future__ import annotations
from pygame.font import SysFont, init
from collections import namedtuple
from typing import List
from itertools import chain

import re

from render_object import RenderText, RenderObject, RenderChildren, RenderBlock, RenderInline

# Default fonts
# TODO: could be moved to a configuration file
FONT = 'verdana'
FONT_BOLD = 'verdanabold'
FONT_ITALIC = 'verdanaitalic'
FONT_BOLD_ITALIC = 'verdanabolditalic'

# List of supported font sizes
# in case user chooses a font_size outside it, the closest one is used instead
SUPPORTED_FONT_SIZES = [11, 13, 16, 19, 24, 32, 40]

FontType = namedtuple('FontType', ['font_size', 'font_weight', 'font_style'])


def initialize_fonts():
    init()  # Initialize pygame fonts
    supported_fonts = {}  # map of supported fonts
    for _font_size in SUPPORTED_FONT_SIZES:
        supported_fonts[FontType(_font_size, 'normal', 'normal')] = SysFont(FONT, _font_size)
        supported_fonts[FontType(_font_size, 'bold', 'normal')] = SysFont(FONT_BOLD, _font_size)
        supported_fonts[FontType(_font_size, 'normal', 'italic')] = SysFont(FONT_ITALIC, _font_size)
        supported_fonts[FontType(_font_size, 'bold', 'italic')] = SysFont(FONT_BOLD_ITALIC, _font_size)

    def _get_font(font_size: int, font_weight: str, font_style: str):
        assert font_weight in ['normal', 'bold'] and font_style in ['normal', 'italic']

        # Get the closest supported font size
        font_size = min(SUPPORTED_FONT_SIZES, key=lambda size: abs(font_size - size))
        return supported_fonts[FontType(font_size, font_weight, font_style)]

    return _get_font


# Get font is used to get the closest supported font
get_font = initialize_fonts()


# WordObject, LineObject and RenderLines will be utilized during the layout and painting phases
# They are also render objects, they are used to handle texts
# And are utilized in Layout phase in place of RenderInline and RenderTexts

class WordObject(RenderObject):
    # WordObject represents a word withing a render text
    def __init__(self, word: str, ro: RenderText):
        # Keep track of the word and render text it's part of
        self.word = word
        self.text_object = ro
        font = get_font(ro.font_size, ro.font_weight, ro.font_style)
        self.font = font  # get the pygame font, will be used later why painting
        self.size = font.size(word)  # Compute the layout space it occupies

    @property
    def width(self):
        return self.size[0]

    @property
    def height(self):
        return self.size[1]

    def __repr__(self):
        return f'WordObject({self.word!r}, size={self.size})'


class LineObject(RenderChildren):
    # LineObject is a list of WordObjects that will be rendered on the same line
    children: List[WordObject]

    def __init__(self):
        RenderChildren.__init__(self)

    @property
    def width(self):  # Width needed by the line - sum of all word widths
        return sum(wo.width for wo in self.children)

    @property
    def height(self):  # Height of the line - max of all word heights
        return max(wo.height for wo in self.children)

    def __str__(self):
        words = ', '.join(map(str, self.children))
        return f'LineObject({words})'

    def __repr__(self):
        return f'LineObject(num_words={len(self.children)})'

    @property
    def num_words(self):
        return len(self.children)


class RenderLines(RenderChildren):
    # RenderLines is a list of all RenderLines resulting from children of a
    # RenderBlock whose descendants are all inline or text objects
    children: List[LineObject]

    def __init__(self):
        RenderChildren.__init__(self)

    @property
    def width(self):  # Width is max of all lines widths
        return max(lo.width for lo in self.children)

    @property
    def height(self):  # height is sum of all line heights
        return sum(lo.height for lo in self.children)

    @property
    def num_lines(self):
        return len(self.children)

    @property
    def num_words(self):
        return sum(lo.num_words for lo in self.children)

    def __str__(self):
        lines = ', '.join(map(str, self.children))
        return f'RenderLines({lines})'

    def __repr__(self):
        return f'RenderLines(num_lines={self.num_lines},num_words={self.num_words},size=({self.width},{self.height}))'


def compute_word_objects(text_object: RenderText):
    # Takes RenderText and constructs word objects from the it's text

    # Splits the text within into words
    # Input: 'Hello world! How are you?'
    # Output: ['Hello ', 'world! ', 'How ', 'are ', 'you?']
    words = list(filter(lambda _: _, re.split(r'(?<=\s)', text_object.node.text)))
    # Construct word objects from those words
    text_object.words = [WordObject(word, text_object) for word in words]
    return text_object.words


def construct_lines_object(word_objects: List[WordObject], available_width: int):
    # If some word is greater than available width, we'll use that as the width
    width = max(available_width, max(wo.width for wo in word_objects))
    lines_object = RenderLines()
    line_object = None
    for wo in word_objects:
        if line_object and line_object.width + wo.width <= width:
            # If word can be accommodated in existing line
            line_object.add_child(wo)
        else:
            # If line doesn't exist or can't be accommodated
            # Create a new line with that word
            line_object = LineObject()
            line_object.add_child(wo)
            lines_object.add_child(line_object)
    return lines_object


def construct_render_lines(block_object: RenderBlock, available_width: int):
    # expects a block object whose child are all inline or text objects
    # Constructs a RenderLines object, with the words populated from the RenderText descendants
    # How many word can be accommodated in a given line is determined by the available width
    # however if available_width is less than max word width, then later is preferred

    # all it's descents must be inline or text objects, though condition only checks for its children
    assert block_object.children and \
           all(not isinstance(child_ro, RenderBlock) for child_ro in block_object.children)

    text_objects = []  # list of text object descendants in `block_object` in in-order depth first traversal
    render_objects = [block_object]  # Note `block_object` will be the only expected block object in this list
    # `render_objects` will contain inline objects from which text objects must be obtained recursively
    while render_objects:
        ro = render_objects.pop(0)  # In-order Depth first traversal to obtain the text objects
        # Obtain all the text element children of inline element
        text_objects.extend(child_ro for child_ro in ro.children if isinstance(child_ro, RenderText))
        # Descendants of inline objects need traversal
        inline_objects = [child_ro for child_ro in ro.children if isinstance(child_ro, RenderInline)]
        render_objects = inline_objects + render_objects

    # Aggregate words from each of the text objects
    word_objects = list(chain.from_iterable(compute_word_objects(text_object) for text_object in text_objects))

    # Construct render lines object from the word objects based on available width
    # Note: all words needs to passed at one go to construct the render lines objects
    block_object.lines_object = construct_lines_object(word_objects, available_width)
    return block_object.lines_object
