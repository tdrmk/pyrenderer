from css_properties import *


def get_line_no(text: str, index: int):
    # Returns the line and column number of the given index.
    previous_text = text[:index + 1]
    lines = previous_text.count('\n')
    last_line = previous_text[previous_text.rfind('\n') + 1:]
    # line number, column number
    return lines, len(last_line)


def print_tree(root):
    # Recursively prints a tree structure,
    # uses `str` function to print the node
    # expects the node to have `children` attribute
    def __print(node, prefix='|', last=True):
        current_prefix = prefix
        if last:
            prefix = prefix[:-1] + ' '
            current_prefix = prefix[:-1] + '`'
        print(f'{current_prefix}---{str(node)}')
        try:
            for child in node.children:
                if node.children[-1] == child:
                    __print(child, prefix + '\t|', True)
                else:
                    __print(child, prefix + '\t|', False)
        except AttributeError:
            # When node has no children
            pass

    __print(root)


def format_styles(styles: dict):
    # converts parsed style (in attachment step) into string
    if not styles:
        return ''
    return f'width: {styles[WIDTH]}, height: {styles[HEIGHT]}, ' \
        f'margin: {styles[MARGIN_TOP]} {styles[MARGIN_RIGHT]} {styles[MARGIN_BOTTOM]} {styles[MARGIN_LEFT]}, ' \
        f'padding: {styles[PADDING_TOP]} {styles[PADDING_RIGHT]} {styles[PADDING_BOTTOM]} {styles[PADDING_LEFT]}, ' \
        f'border: {styles[BORDER_TOP]} {styles[BORDER_RIGHT]} {styles[BORDER_BOTTOM]} {styles[BORDER_LEFT]} ' \
        f'{styles[BORDER_COLOR]}, ' \
        f'display: {styles[DISPLAY]}, ' \
        f'position: {styles[POSITION]} {styles[TOP]} {styles[RIGHT]} {styles[BOTTOM]} {styles[LEFT]}, '\
        f'font: {styles[FONT_SIZE]} {styles[FONT_WEIGHT]} {styles[FONT_STYLE]}, ' \
        f'color: {styles[COLOR]} {styles[BACKGROUND_COLOR]}'
