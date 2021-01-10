import argparse
import os
import sys
import pygame

import html_parser
import css_parser
import attachment
import renderer
import layout
import paint
import utils

# Obtain the HTML and CSS file names from cli
parser = argparse.ArgumentParser(description='A Browser Rendering Engine')
parser.add_argument('--html', type=str, default='index.html', help='html page to render', )
parser.add_argument('--css', type=str, default=[], nargs='*', help='stylesheets for styling html page')
args = parser.parse_args()

html_file = args.html
style_sheet_files = ['agent.css'] + args.css
DEFAULT_BROWSER_BACKGROUND = (255, 255, 255)
WIDTH, HEIGHT = 1000, 600

# Make sure all specified files exists
for file in [html_file] + style_sheet_files:
    if not os.path.exists(file):
        print(f'Cannot find {file}', file=sys.stderr)
        exit()


def construct_layout_tree(html_page, style_sheets, window_width: int, window_height: int):
    with open(html_page) as f_html:
        # construct DOM tree from html
        dom = html_parser.parse(f_html.read())
        page_title = html_parser.get_page_title(dom)
        utils.print_tree(dom)

        # construct css object model
        cssom = None
        for style_sheet in style_sheets:
            with open(style_sheet) as f_css:
                cssom = css_parser.parse(f_css.read(), cssom)

        # apply styles
        attachment.attach_styles(dom, cssom)

        # construct render tree
        render_tree = renderer.construct_render_tree(dom)
        utils.print_tree(render_tree)

        # construct layout
        layout.construct_layout(render_tree, window_width, window_height)

        # render tree can now be painted
        return render_tree, page_title


def main_loop(render_tree, title, width, height, fps=60):
    pygame.init()

    win = pygame.display.set_mode((width, height))
    pygame.display.set_caption(title)
    clock = pygame.time.Clock()

    run = True
    while run:
        for event in pygame.event.get():
            if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_q):
                run = False

        win.fill(DEFAULT_BROWSER_BACKGROUND)
        # just paint the render tree onto `win`
        paint.paint_layout(win, render_tree)
        pygame.display.update()

        clock.tick(fps)

    pygame.quit()


if __name__ == '__main__':
    final_render_tree, html_page_title = construct_layout_tree(html_file, style_sheet_files, WIDTH, HEIGHT)
    main_loop(final_render_tree, html_page_title, WIDTH, HEIGHT)