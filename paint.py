import pygame
from box_model import BoxModel
from render_object import RenderBlock
from text_layout import RenderLines
from collections import namedtuple

# Colors while drawing layout
BOX_OUTLINE_COLOR = (220, 20, 60)
BORDER_OUTLINE_COLOR = (255, 165, 0)
PADDING_OUTLINE_COLOR = (30, 144, 255)
CONTENT_OUTLINE_COLOR = (65, 105, 225)


# Note: all the paint functions expect the box_model's left and right values to be set
def paint_box_model_layout(win: pygame.Surface, bm: BoxModel):
    # Draw the layout of specified box model
    pygame.draw.rect(win, BOX_OUTLINE_COLOR, bm.box_rect, 1)
    pygame.draw.rect(win, BORDER_OUTLINE_COLOR, bm.border_rect, 1)
    pygame.draw.rect(win, PADDING_OUTLINE_COLOR, bm.padding_rect, 1)
    pygame.draw.rect(win, CONTENT_OUTLINE_COLOR, bm.content_rect, 1)


def paint_render_lines(win: pygame.Surface, render_lines: RenderLines, left: int, top: int):
    # Paint the words in the `render_lines` object
    # Note: left and top are absolute positions with respect to `win`
    line_offset = 0  # vertical offset
    for line_object in render_lines.children:
        line_height = line_object.height
        word_offset = 0  # horizontal offset
        for word_object in line_object.children:
            # Note: when background is None, no background is rendered
            text_surface = word_object.font.render(word_object.word, True, word_object.text_object.color,
                                                   word_object.text_object.background_color)
            # correction factor to align the word to the center of the line
            alignment_correction = (line_height - word_object.height) // 2
            text_top = top + line_offset + alignment_correction
            text_left = left + word_offset
            win.blit(text_surface, (text_left, text_top))
            word_offset += word_object.width
        line_offset += line_height


def paint_box_model(win: pygame.Surface, bm: BoxModel, ro: RenderBlock):
    # Draw background (including content and padding) and border
    if ro.background_color:
        # Fill with background color
        pygame.draw.rect(win, pygame.Color(ro.background_color), bm.padding_rect, 0)

    # For borders, we need to draw lines around the content
    # Note some correction factors are added to make borders precise
    # For default behaviour refer: https://www.pygame.org/docs/ref/draw.html#pygame.draw.line
    Border = namedtuple('Border', ['start_position', 'end_position', 'border_width'])
    borders = [
        Border((bm.left + bm.margin_left, bm.top + bm.margin_top + (bm.border_top - 1) // 2),
               (bm.right - bm.margin_right - 1, bm.top + bm.margin_top + (bm.border_top - 1) // 2),
               bm.border_top),  # Border Top
        Border((bm.right - bm.margin_right - (bm.border_right + 3) // 2, bm.top + bm.margin_top),
               (bm.right - bm.margin_right - (bm.border_right + 3) // 2, bm.bottom - bm.margin_bottom - 1),
               bm.border_right),  # Border Right
        Border((bm.left + bm.margin_left, bm.bottom - bm.margin_bottom - (bm.border_bottom + 3) // 2),
               (bm.right - bm.margin_right - 1, bm.bottom - bm.margin_bottom - (bm.border_bottom + 3) // 2),
               bm.border_bottom),  # Border Bottom
        Border((bm.left + bm.margin_left + (bm.border_left - 1) // 2, bm.top + bm.margin_top),
               (bm.left + bm.margin_left + (bm.border_left - 1) // 2, bm.bottom - bm.margin_bottom - 1),
               bm.border_left),  # Border Left
    ]
    for start_position, end_position, border_width in borders:
        if border_width > 0:
            pygame.draw.line(win, pygame.Color(ro.border_color), start_position, end_position, border_width)


def paint_layout(win: pygame.Surface, root_ro: RenderBlock, show_layout=False):
    # Paint the render tree after layout stage onto `win`
    # show_layout -> if enabled show only layout lines
    def draw_block(ro: RenderBlock):
        if show_layout:
            paint_box_model_layout(win, ro.box_model)
        else:
            paint_box_model(win, ro.box_model, ro)
            try:  # paint text if any
                paint_render_lines(win, ro.lines_object, ro.box_model.content_left, ro.box_model.content_top)
            except AttributeError:  # thrown from ro.lines_object
                pass

    # While painting, first static and relatively positioned elements are drawn
    # then absolutely positioned and finally fixed elements
    # Note: static, relative and absolute positioned elements move on scrolling
    # while fixed stays fixed to viewport
    blocks = [root_ro]
    absolute_blocks = []
    fixed_blocks = []

    # Setting the root level top and left offsets for computing others
    root_ro.box_model.top = 0
    root_ro.box_model.left = 0

    # Note: absolute and fixed elements may have static, relative and absolute elements
    # However will never have fixed elements and all fixed elements are children of viewport (html)
    # Paint all the blocks - priority based painting however
    while blocks + absolute_blocks + fixed_blocks:
        if blocks:
            block = blocks.pop(0)
            assert isinstance(block, RenderBlock)
            if block.parent:
                assert isinstance(block.parent, RenderBlock)
                # Compute the positions from parent
                block.box_model.top = block.parent.box_model.content_top + block.box_model.relative_top
                block.box_model.left = block.parent.box_model.content_left + block.box_model.relative_left

            if block.position == 'static' or block.position == 'relative':
                draw_block(block)
                if all(isinstance(child_ro, RenderBlock) for child_ro in block.children):
                    # Note if blocks have children either they are all block or inline
                    blocks = block.children + blocks
            elif block.position == 'absolute':  # Note the intended order
                absolute_blocks.append(block)
            elif block.position == 'fixed':
                fixed_blocks.append(block)
        elif absolute_blocks:
            block = absolute_blocks.pop(0)
            assert isinstance(block, RenderBlock)
            if block.parent:
                block.box_model.top = block.parent.box_model.content_top + block.box_model.relative_top
                block.box_model.left = block.parent.box_model.content_left + block.box_model.relative_left

            draw_block(block)
            if all(isinstance(child_ro, RenderBlock) for child_ro in block.children):
                # First render the children of this block and its descendants before rendering other of the kind
                # Absolute block is not expected to have fixed children
                blocks = [child_ro for child_ro in block.children if
                          child_ro.position in ['static', 'relative']] + blocks
                absolute_blocks = [child_ro for child_ro in block.children if
                                   child_ro.position == 'absolute'] + absolute_blocks
        elif fixed_blocks:
            # Point to Note: Fixed blocks are not impact by scroll
            block = fixed_blocks.pop(0)
            assert isinstance(block, RenderBlock)
            if block.parent:
                block.box_model.top = block.parent.box_model.content_top + block.box_model.relative_top
                block.box_model.left = block.parent.box_model.content_left + block.box_model.relative_left

            draw_block(block)
            if all(isinstance(child_ro, RenderBlock) for child_ro in block.children):
                # Similar to above, however each of them is prioritized.
                blocks = [child_ro for child_ro in block.children if
                          child_ro.position in ['static', 'relative']] + blocks
                absolute_blocks = [child_ro for child_ro in block.children if
                                   child_ro.position == 'absolute'] + absolute_blocks
