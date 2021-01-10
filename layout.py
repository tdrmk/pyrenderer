from __future__ import annotations
from render_object import RenderBlock
from css_properties import *
from text_layout import construct_render_lines
from box_model import BoxModel
import re


def compute_width(css_width: str, available_width: int, allow_auto=False):
    if re.match(r'^\d+px$', css_width):
        return int(css_width[:-2])
    elif re.match(r'^\d+%$', css_width):
        return available_width * int(css_width[:-1]) // 100
    elif allow_auto and css_width == 'auto':  # in case auto is allowed, its value to zero
        return 0
    raise Exception(f'Unknown width format {css_width!r}')


# Note: currently only using border-box for box sizing (this is set to default unlike in browser)
def compute_box_model_properties(ro: RenderBlock, available_width: int, available_height: int, box_sizing='border-box'):
    # Computes box model properties that depends only on available_width and available_height (ie containing box)
    # Most box model properties can be computed, however height depending on its value needs the height of children

    # Note most properties are dependent on available width, unlike expectations
    # since height is not available upfront is most cases
    # following box model properties values are in either px or %
    ro.box_model.margin_left = compute_width(ro.node.styles[MARGIN_LEFT], available_width)
    ro.box_model.margin_right = compute_width(ro.node.styles[MARGIN_RIGHT], available_width)
    ro.box_model.margin_top = compute_width(ro.node.styles[MARGIN_TOP], available_width)
    ro.box_model.margin_bottom = compute_width(ro.node.styles[MARGIN_BOTTOM], available_width)

    ro.box_model.padding_left = compute_width(ro.node.styles[PADDING_LEFT], available_width)
    ro.box_model.padding_right = compute_width(ro.node.styles[PADDING_RIGHT], available_width)
    ro.box_model.padding_top = compute_width(ro.node.styles[PADDING_TOP], available_width)
    ro.box_model.padding_bottom = compute_width(ro.node.styles[PADDING_BOTTOM], available_width)

    ro.box_model.border_left = compute_width(ro.node.styles[BORDER_LEFT], available_width)
    ro.box_model.border_right = compute_width(ro.node.styles[BORDER_RIGHT], available_width)
    ro.box_model.border_top = compute_width(ro.node.styles[BORDER_TOP], available_width)
    ro.box_model.border_bottom = compute_width(ro.node.styles[BORDER_BOTTOM], available_width)

    if ro.node.styles[WIDTH] == 'auto':
        # In case of auto, box model occupies available space
        # ie content width is computed by subtracting margin, border and padding widths
        ro.box_model.box_width = available_width
    else:
        # Based on box-sizing, width will either include or exclude padding and border
        # Note: margin is included in neither of the models
        # https://developer.mozilla.org/en-US/docs/Web/CSS/box-sizing

        if box_sizing == 'border-box':  # Box-sizing - border-box - width includes padding and border
            ro.box_model.width = compute_width(ro.node.styles[WIDTH], available_width)
        else:  # Box-sizing - content-box - width of the content
            ro.box_model.content_width = compute_width(ro.node.styles[WIDTH], available_width)

    if ro.node.styles[HEIGHT] != 'auto':  # `height: auto` needs height of children
        if box_sizing == 'border-box':  # Box-sizing - border-box
            ro.box_model.height = compute_width(ro.node.styles[HEIGHT], available_height)
        else:  # Box-sizing - content-box
            ro.box_model.content_height = compute_width(ro.node.styles[HEIGHT], available_height)


def compute_box_model_height(ro: RenderBlock, available_height: int, children_height: int, box_sizing='border-box'):
    if ro.node.styles[HEIGHT] == 'auto':
        ro.box_model.content_height = children_height
    else:
        # Duplicate of above
        if box_sizing == 'border-box':
            ro.box_model.height = compute_width(ro.node.styles[HEIGHT], available_height)
        else:  # Box-sizing - content-box
            ro.box_model.content_height = compute_width(ro.node.styles[HEIGHT], available_height)


# Define two ways to construct layout - recursive or iterative
# Using the iterative manner to support converting it to a generator function


def construct_layout(root_ro: RenderBlock, window_width: int, window_height: int):
    assert root_ro.node.tag == 'html' and root_ro.position == 'relative'
    # block elements needing layout computation
    render_blocks = [root_ro]  # Always contains block elements

    # Mainly from blocks with `height: 'auto'` that have children
    # But also all blocks that have children to compute children's relative positioning within it
    # note ordering is important, blocks at the topological order
    # blocks on top of the hierarchy are in the beginning of the list
    blocks_needing_height = []

    # also track positioned elements as they need positioning based on parent
    # note: we only need them for absolutes and fixed when `bottom` and `right`
    # are specified. For simplicity we compute them for all cases later.
    positioned_elements = []

    while render_blocks:  # pre-order depth-first traversal
        ro = render_blocks.pop(0)
        assert isinstance(ro, RenderBlock)  # expect only block
        if not ro.parent:  # handling initial case
            assert ro == root_ro
            width, height = window_width, window_height
        else:
            # width, (possibly) height of parent must of computed before children (pre-order traversal)
            assert isinstance(ro.parent, RenderBlock)
            width, height = ro.parent.box_model.content_width, ro.parent.box_model.content_height

        # pre-processing
        if ro.parent and ro.parent.node.styles[HEIGHT] == 'auto' and \
                re.match(r'^\d+%$', ro.node.styles[HEIGHT]):
            # if parent's height is `auto`, and current blocks's height is in `percent`
            # then blocks height is also resolved to `auto`
            # https://developer.mozilla.org/en-US/docs/Web/CSS/height#Formal_definition
            ro.node.styles[HEIGHT] = 'auto'

        if ro.is_positioned:  # collect positioned elements
            positioned_elements.append(ro)

        ro.box_model = BoxModel()  # <---------- Box Model set in layout phase
        # Compute box model properties that don't need children information
        compute_box_model_properties(ro, width, height)
        if not ro.children:  # if not children and `auto`, `children_height` is resolved to 0
            compute_box_model_height(ro, height, children_height=0)
        elif all(not isinstance(child_ro, RenderBlock) for child_ro in ro.children):
            # if none of the children are block elements, then height can be resolved
            # of the underlying text objects
            # Note: since underlying text is its children, content_width is used
            lines_object = construct_render_lines(ro, ro.box_model.content_width)
            # Compute the height if `auto`
            compute_box_model_height(ro, height, children_height=lines_object.height)
        else:
            # all its children expected to be block objects
            assert ro.children and all(isinstance(child_ro, RenderBlock) for child_ro in ro.children)

            # in case height is auto, its height can be computed only
            # after it's children's height has been computed
            # also its children needs relative positioning
            blocks_needing_height.append(ro)

            # Compute box-model properties of its children first in order of occurrence
            render_blocks = ro.children[:] + render_blocks

    # compute the height's of blocks based on it's children if height is `auto`
    # also compute relative positioning of its children in either case
    while blocks_needing_height:
        # pickup elements from lower down in the tree first
        ro = blocks_needing_height.pop()
        children_height = 0
        for child_ro in ro.children:
            assert isinstance(child_ro, RenderBlock)
            child_ro.box_model.relative_left = 0
            child_ro.box_model.relative_top = children_height
            if child_ro.position == 'static' or child_ro.position == 'relative':
                # only static and relative positioned children contributes to parent height
                # note: relative positioned elements will be moved later without affecting parent height
                children_height += child_ro.box_model.box_height
        if ro.node.styles[HEIGHT] == 'auto':
            # in case of auto compute height based on accumulated children height
            compute_box_model_height(ro, 0, children_height)

    # Compute relative positions of positioned elements
    while positioned_elements:
        # Note only relative positioning is set in layout phase
        ro = positioned_elements.pop()
        if ro.parent:
            if ro.position == 'relative':
                top = compute_width(ro.node.styles[TOP], ro.parent.box_model.content_width, allow_auto=True)
                left = compute_width(ro.node.styles[LEFT], ro.parent.box_model.content_width, allow_auto=True)
                bottom = compute_width(ro.node.styles[BOTTOM], ro.parent.box_model.content_width, allow_auto=True)
                right = compute_width(ro.node.styles[RIGHT], ro.parent.box_model.content_width, allow_auto=True)
                # Move it relatively with respect to its current position
                ro.box_model.relative_top += top - bottom
                ro.box_model.relative_left += left - right
            else:  # in case of absolute and fixed
                if ro.node.styles[TOP] != 'auto':
                    top = compute_width(ro.node.styles[TOP], ro.parent.box_model.content_width)
                    ro.box_model.relative_top = top
                if ro.node.styles[LEFT] != 'auto':
                    left = compute_width(ro.node.styles[LEFT], ro.parent.box_model.content_width)
                    ro.box_model.relative_left = left

                # bottom and right have higher priority than top and left ? (Mostly nope)
                if ro.node.styles[BOTTOM] != 'auto':
                    bottom = compute_width(ro.node.styles[BOTTOM], ro.parent.box_model.content_width)
                    ro.box_model.relative_top = ro.parent.box_model.content_height - ro.box_model.box_height - bottom
                if ro.node.styles[RIGHT] != 'auto':
                    right = compute_width(ro.node.styles[RIGHT], ro.parent.box_model.content_width)
                    ro.box_model.relative_left = ro.parent.box_model.content_width - ro.box_model.box_width - right
