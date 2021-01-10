from __future__ import annotations
from html_parser import DOMNode, TextNode
from attachment import parse_style, inherit_style
from render_object import RenderBlock, RenderInline, RenderText
from css_properties import DISPLAY


def anonymous_block(parent_node: DOMNode):
    # Creates a anonymous render block,
    # uses the parent node to compute inherited styles,
    # NOTE: the corresponding dom node has no parent as its not part of DOM
    node = DOMNode('div', attributes={}, token=None)
    node.styles = parse_style({DISPLAY: 'block'})
    node.parent = parent_node  # only add it to compute inherited styles
    inherit_style(node)
    node.parent = None  # remove it after computing inherited styles
    return RenderBlock(node)


def construct_render_tree(dom: DOMNode):
    # TODO: Fix issue in DF traversal, but works
    # Returns a render tree
    #   - with no display none elements
    #   - block objects contain either all inline/text objects or block objects
    #   - inline objects contain only inline/text objects
    #   - absolute and fixed block objects are children of
    #     positioned ancestor block object and viewport respectively
    assert dom.styles[DISPLAY] == 'block'

    root_ro = RenderBlock(dom)
    # Construct the initial render tree
    #   - removes display none blocks
    #   - block elements are only children of block elements
    #   - inline and text elements can be children of both inline and block elements
    render_objects = [root_ro]
    while render_objects:
        ro = render_objects.pop(0)  # Depth first traversal
        for node in ro.node.children:
            if isinstance(node, TextNode):
                # text is a leaf node, insert it to the parent.
                text_ro = RenderText(node)
                ro.add_child(text_ro)
                continue

            assert isinstance(node, DOMNode)
            if node.styles[DISPLAY] == 'none':
                # Ignore the node and its children
                continue

            elif node.styles[DISPLAY] == 'block':
                block_ro = RenderBlock(node)
                if ro.node.styles[DISPLAY] == 'inline':
                    # If parent is a inline block,
                    # can't render a block element inside it
                    # find an ancestor who's a block element
                    # and add the block as it child,
                    # sibling to the inline element
                    # Input: <div> <span> <span> <div> A BLOCK ELEMENT </div> </span> </span> <div> </div> </div>
                    # Expected: <div> <span> <span> </span> </span> <div> A BLOCK ELEMENT </div> <div> </div> </div>
                    ancestor_ro, inline_sibling = ro, None
                    while ancestor_ro.node.styles[DISPLAY] != 'block':
                        # go above in the parent chain
                        ancestor_ro, inline_sibling = ancestor_ro.parent, ancestor_ro
                        assert ancestor_ro
                    # insert into the ancestor children after inline_sibling
                    ancestor_ro.insert_after(block_ro, inline_sibling)
                else:
                    ro.add_child(block_ro)
                render_objects = [block_ro] + render_objects

            elif node.styles[DISPLAY] == 'inline':
                inline_ro = RenderInline(node)
                ro.add_child(inline_ro)
                render_objects = [inline_ro] + render_objects

    # Move absolute and fixed render blocks up the ancestor chain
    # absolute block elements become the children of nearest positioned ancestor
    # fixed block elements become children of viewport (html render block)
    # NOTE: POSITIONS OF INLINE OBJECTS ARE IGNORED.
    assert root_ro.position == 'relative'
    render_objects = [root_ro]
    while render_objects:
        ro = render_objects.pop(0)  # Depth first traversal
        for child_ro in ro.children:
            if not isinstance(child_ro, RenderBlock):
                continue

            # Only handling block elements
            if child_ro.position == 'absolute':
                if not ro.is_positioned:
                    # find the nearest positioned ancestor
                    ancestor_ro = ro
                    while not ancestor_ro.is_positioned:
                        ancestor_ro = ancestor_ro.parent
                        assert ancestor_ro
                    # remove from current parent
                    ro.remove_child(child_ro)
                    # adopted by the positioned ancestor
                    ancestor_ro.add_child(child_ro)
            elif child_ro.position == 'fixed':
                if ro != root_ro:
                    # remove from current parent
                    ro.remove_child(child_ro)
                    # move it to the viewport (html)
                    root_ro.add_child(child_ro)

            render_objects = [child_ro] + render_objects

    # When blocks objects have both inline and block objects as children
    # we group inline blocks ino an anonymous block object
    # https://www.w3.org/TR/CSS22/visuren.html#anonymous-block-level
    # INPUT: <BLOCK> <INLINE /> <INLINE /> <BLOCK /> <INLINE /> </BLOCK>
    # EXPECTED: <BLOCK>
    #               <ANONYMOUS-BLOCK> <INLINE /> <INLINE /> </ANONYMOUS-BLOCK>
    #               <BLOCK />
    #               <ANONYMOUS-BLOCK> <INLINE /> </ANONYMOUS-BLOCK>
    #           </BLOCK>
    render_objects = [root_ro]
    while render_objects:
        ro = render_objects.pop(0)  # Depth first traversal
        if ro.children and any(isinstance(child_ro, RenderBlock) for child_ro in ro.children) and \
                any(not isinstance(child_ro, RenderBlock) for child_ro in ro.children):
            # If has children that's a mixture of block and inline elements
            children = ro.abandon_children()  # abandon children to recompute it
            anonymous_ro = None
            # NOTE: the anonymous block always has inline or text elements!
            for child_ro in children:
                if isinstance(child_ro, RenderBlock):
                    ro.add_child(child_ro)  # re-add the block element as child
                    anonymous_ro = None
                    continue
                # If a inline or text object
                if not anonymous_ro:
                    anonymous_ro = anonymous_block(ro.node)
                    ro.add_child(anonymous_ro)  # add the anonymous block at child
                # add the inline or text object into the anonymous block
                assert isinstance(child_ro, RenderInline) or isinstance(child_ro, RenderText)
                anonymous_ro.add_child(child_ro)
        # Loop through (updated) children
        # Note since anonymous block only has inline/text objects,
        # it will not trigger further recursion.
        for child_ro in ro.children:
            if isinstance(child_ro, RenderBlock):
                render_objects = [child_ro] + render_objects

    return root_ro
