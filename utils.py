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
