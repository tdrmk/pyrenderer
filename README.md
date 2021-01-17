# A Browser Rendering Engine in Python

## INTRODUCTION
This project implements a simplified browser rendering engine in python.
Uses pygame as the UI backend for painting and layout (of text).

![Sample Image](sample.png)

The project only supports a limited subset of HTML and CSS. 

### HTML

- All elements must be either self-closing or have start and end tags
- Supports comments and doctype declaration.
- Supports text
- Supports only `id` and `class` attributes, and ignores remaining.
    - element can have multiple classes (space separated list)
- Does not support different tag contexts (like _script_)
- Tag names can be anything. 
    - However by default elements with unknown tags have `display: none`.
    - `display` property must be set in user style sheets for other elements.
- Handles some amount of missing/erroneous end tags
 
### CSS

- Supports multiple CSS files.
- Browser (default) styles are defined in `agent.css`
- Only simple selectors are supported 
    - universal, tag, id and class selectors (eg, `*`, `div`, `.class`, `#id`). 
- Each CSS rule must have only one selector
- Supports Cascading, Specificity and Inheritance.
    - Specificity is limited by selectors supported
- Supported CSS properties can be found at `css_properties.py`.
    - box-model properties: 
    `margin-top`, `margin-bottom`, `margin-left`, `margin-right`,
    `padding-top`, `padding-bottom`, `padding-left`, `padding-right`,
    `border-top-width`, `border-bottom-width`, `border-bottom-left`, `border-bottom-right`,
    `width`, `height`, `top`, `bottom`, `left`, `right`.
    - colors: `color`, `background-color`, `border-color`
    - fonts: `font-size`, `font-weight`, `font-style`
    - layout: `display`, `position`
- Supports `display` types of `none`, `block` and `inline`
- Supports `position` types of `static`, `relative`, `absolute` and `fixed`.
- Box model properties can be specified as `auto`, or in pixels `px` or in percentage `%`
- Colors (`color`, `background-color`, `border-color`) must be in RGB (eg, `#ffffff`). 
    - `background-color` can also be `transparent`
- `font-size` must be in pixels `px`. `font-weight` can be `normal` or `bold`. 
  `font-style` can be `normal` or `italic`
- Some properties can be inherited (value is `inherit`). 
    - `color`, `background-color`, `border-color`, `font-size`, `font-weight`, `font-style`

## SETUP

Needs python 3.8 or above.

Install dependencies using:

    pip install -r requirements.txt

Run the program using
    
    python main.py --html index.html --css index.css

For more options

    python main.py --help

Note: Program supports multiple CSS files.

## Implementation Details

A Modern Browser has several major components each performing different functions. 
Rendering Engine is one of them which parses HTML and CSS and displays it onto the screen.
Different browsers use different rendering engines, like firefox uses Gecko, etc. 

Rendering typically involves the following steps:
1. Constructing a DOM tree from HTML, enriching the styles from CSS
2. Constructing a render tree, consisting of nodes that will we displayed on the screen.
3. Computing the layout of the render tree, ie, computing the sizes and positions of the nodes on the screen.
4. Painting the render tree onto the screen.

These steps are performed by different sub-components of the rendering engine.
Following are the sub-components of this simplified rendering engine:
1. HTML Parser
2. CSS Parser
3. Attachment
4. Renderer
5. Layout
6. Paint

### HTML Parser
Parses HTML contents and generates a DOM tree.
It consists of a tokenizer and a parser

**Tokenizer** converts the HTML content into a stream of tokens of different kinds.
Tokens are extracted using regular expressions. 
Token kinds are start tags, end tags, self-closing tags, text, comments, doctype and spaces.
Comments, doctype and spaces tokens are ignored. Rest are used to construct the DOM tree. 
Start tag and self-closing tag tokens can also have attributes (map of key-value pairs) extracted from HTML.

Additionally, all tag names, attribute key-value pairs are converted into lower case. 
Excessive spaces from text are also removed and text is trimmed.

```python
class Token:
    kind: str   # type of token
    value: str
    attributes: dict[str, str]
```


**Parser** constructs DOM tree from the token stream. 
Implementation uses algorithm similar to *Matching Parentheses Problem* (stack based algorithm).
DOM tree consist of two type of nodes, `DOMNode` and `TextNode`.
Current implementation does not distinguish different HTML elements and all are representing using `DOMNode`.
`TextNode` contains text and can only be leaf nodes in the DOM tree.
Only `id` and `class` attributes are currently utilized (for CSS selectors) and rest are ignored.
Parser does not understand different contexts and different tags that are prescribed in the HTML W3 Standard to simplify implementation.
User thus can define any tag name. However, the default browser styles assign `display: none` to unknown HTML elements (in attachment step).
Parser expects end tag for each of the start tag.
However implements error handling for missing close tags and erroneous closing tags.
DOM nodes have parent and children properties to support bi-directional traversal of the tree.  
```python
class DOMNode:
    parent: DOMNode
    children: list[DOMNode]
    id: str
    classes: list[str]

class TextNode:
    parent: DOMNode
    text: str
```


### CSS Parser
Parses style sheets (typically multiple) and constructs a CSS Object Model or CSSOM.
CSS Rules are extracted from the files top to bottom and in the order in which files are listed to support cascading.
CSS Rule consist of a selector and a map of css property and value (to simplify property overriding).
CSSOM maintains a unique CSS Rule for each selector. 
Properties from CSS Rules parsed later override the former (cascading). 
To simplify specificity model, CSS Rules are organized into different maps based on selector types
(universal, tag based, id based and class based) in CSSOM.
Browser CSS (`agent.css`) is first parsed to define default styles. And user's style sheets override them later.
To simply parsing, comments are removed from CSS before top-down parsing.

```python
class CSSRule:
    selector: str
    declarations: dict[str, str]    # css property name to value

class CSSOM:
    # CSS rules grouped based on selector
    universal_rule: CSSRule # selector '*'
    tag_rules: dict[str, CSSRule]   # Tag selectors
    class_rules: dict[str, CSSRule] # Class selectors
    id_rules: dict[str, CSSRule]    # ID selectors
```

### Attachment
Computes styles for DOM nodes using CSSOM.
Traverses the DOM tree, computes style for each DOM node.
For each DOM node, first, universal styles are applied, then tag-based styles are applied (if any).
Later class-based styles are applied in the order of the classes (if any) and finally id-based styles are applied (if any).
Previous values are overridden by new values for properties in each step.

Only supported styles are finally extracted. Checks for supported values for properties, if not overridden with default styles.
Then inheritance is resolved, ie, if value is inherit, parent's style is used (note parent's style is known by traversal order)

```python
class DOMNode:
    styles: dict[str, str]  # Computed styles for DOMNode
```

### Renderer
Constructs render tree from DOM tree, consisting of nodes (called `render objects`) that will be rendered.
Traverses the DOM tree in a pre-order depth first manner to construct render tree.
DOM Nodes (and their children) with `display: none` are not added to render tree.
Render Tree consist of render objects of types RenderBlock (for DOMNode with `display: block`), 
RenderInline (for DOMNode with `display: inline`) and RenderText (for TextNode).
RenderInline cannot have RenderBlocks as children, if in that case, RenderBlock is moved up the tree to become sibling of the RenderInline 
(or its ancestor whose parent is a RenderBlock).
RenderInline can only contain other RenderInline or RenderTexts as children.
RenderBlocks with `position: fixed` are moved up the tree to become the children of the `html` RenderBlock (the viewport).
RenderBlocks with `position: absolute` are moved up the tree till they become children of positioned RenderBlocks (position is `relative`, `fixed` or `absolute`).
Note `html` RenderBlock is always positioned (`position: relative`).
If any RenderBlock contains a mixture of RenderBlocks and other render objects, Anonymous RenderBlocks (RenderBlocks with no associated DOMNode in the DOM tree)
are introduced in the render tree to make sure that RenderBlocks only have either RenderBlocks or non RenderBlocks as children. 
Refer `renderer.py` for more details.

```python
class RenderBlock:
    node: DOMNode
    parent: RenderBlock
    children: Union[List[RenderBlock], List[Union[RenderInline, RenderText]]]

class RenderInline:
    node: DOMNode
    parent: Union[RenderBlock, RenderInline]
    children: List[Union[RenderInline, RenderText]]

class RenderText:
    node: TextNode
    parent: Union[RenderBlock, RenderInline]
```

### Layout
Renderer constructs a render tree with render objects that will be renderer on the screen. Layout computes the sizes
and positions of the render objects for Paint to draw them onto the screen.

RenderBlocks are drawn as boxes (or rectangles) on the screen. 
Sizes (or Box Model Properties) are computed based on CSS properties and available content area 
(parent's content width and content height). 
Positions are absolute positions (x, y coordinates) at which boxes will be drawn on the screen.

Box Model consist of padding, margin, border, width and height.

Layout computes the box model properties of RenderBlocks by traversing the render tree in a pre-order depth first traversal.
Box model properties of HTML RenderBlock (the viewport) is computed based on screen width and height.
Box model properties like padding, border, margin and width are computed based on available width (determined by parent RenderBlock) 
and the specified CSS property value.
Height, when `auto`, is computed based on the height requirements of the children, otherwise is computed based on available height 
(determined by the parent RenderBlock).
Note padding, border and margin, including the ones on the top and bottom, are only dependent on the available width.
When the property values are in pixels `px` then they are used, if they are percentage `%`, 
the values are computed with respect to available width (or available height in case of height).

Height of RenderBlocks which contains no RenderBlocks can be computed by calculating the height required to render the text.
All RenderTexts within such RenderBlocks are extracted (and we determine their font based on `font-size`, `font-weight` and `font-style`).
We then break the texts within into words (and compute the width, height they will occupy). 
We then try to accommodate as words as possible into a line based on available width, 
move the words to the next line if line width exceeds available width. 
We can then determine the number of lines text will occupy and height the text will occupy, 
and determine the height of the parent RenderBlock.
In the implementation, word is represented as WordObject and line as LineObject, and all the lines within a RenderBlock as RenderLines
(Refer `text_layout.py` for more details).

Note positions of positioned (position `relative`, `absolute`, `fixed`) RenderBlocks are computed after computing the heights of parent RenderBlock.

Note if parent RenderBlock's height is `auto`(ie, depends on children height), and current RenderBlock's height is in '%'(ie, depends on parent height).
The RenderBlock's height is also convert to `auto`.

In the implementation, Relative positions of children (with respect to its parent) are computed in the layout phase.
Absolute positions are computed in the paint phase.

```python
class RenderBlock:
    box_model: BoxModel

class BoxModel:
    # box model properties
    padding_left: int
    padding_right: int
    padding_top: int
    padding_bottom: int
    
    border_left: int
    border_right: int
    border_top: int
    border_bottom: int
    
    margin_left: int
    margin_right: int
    margin_top: int
    margin_bottom: int
    
    # content area for children
    content_width: int
    content_height: int    
    
    # positioning
    left: int
    right: int
```

### Paint

Draws the render objects in the render tree onto the screen.
RenderBlocks in the render tree are drawn in a in-order depth first order.
While drawing a RenderBlock first border and background is drawn (at computed positions in box model), 
followed by its children. 
When the RenderBlock contains no RenderBlock children, text within is drawn word by word, line by line, 
as determined in the layout phase.

Note during initial traversal, only RenderBlocks with positions `static` and `relative` are drawn.
When there are no more such blocks to draw, RenderBlocks with position `absolute` are drawn 
(along with its children) in the same traversal order.
Finally RenderBlocks with position `fixed` are drawn (with its children) when no other block to draw.
This ordering makes sure that RenderBlocks with positions `fixed` and `absolute` are drawn on top RenderBlocks
with positions `static` and `relative`.
Refer `paint.py` for the complete algorithm.

## Additional Resources
- [How Browsers Work: Behind the scenes of modern web browsers](https://www.html5rocks.com/en/tutorials/internals/howbrowserswork/)
- [Kruno: How browsers work | JSUnconf 2017](https://www.youtube.com/watch?v=0IsQqJ7pwhw)
- [Ryan Seddon: So how does the browser actually render a website | JSConf EU 2015](https://www.youtube.com/watch?v=SmE4OwHztCc)
- [Let's build a browser engine! - Matt Brubeck](https://limpet.net/mbrubeck/2014/08/08/toy-layout-engine-1.html)
- [Parsing HTML documents - HTML Living Standard](https://html.spec.whatwg.org/multipage/parsing.html)
- [The HTML Syntax - HTML Living Standard](https://html.spec.whatwg.org/multipage/syntax.html)
- [HTML 4.01 Specification](https://www.w3.org/TR/html401/)
- [W3 Introduction to CSS2](https://www.w3.org/TR/WD-CSS2/intro.html)
- [W3 HTML2 DOM IDL Definitions](https://www.w3.org/TR/2003/REC-DOM-Level-2-HTML-20030109/idl-definitions.html)
- [Mozilla CSS Cascade and Inheritance](https://developer.mozilla.org/en-US/docs/Learn/CSS/Building_blocks/Cascade_and_inheritance)
- [Inline elements and Padding - Russ Weakley](https://maxdesign.com.au/articles/inline/)
- [W3 CSS 2 Visual Formatting Model](https://www.w3.org/TR/CSS22/visuren.html)
- [Python re - writing a tokenizer ](https://docs.python.org/3/library/re.html#writing-a-tokenizer)
- [How browser rendering works — behind the scenes - Ohans Emmanuel](https://blog.logrocket.com/how-browser-rendering-works-behind-the-scenes-6782b0e8fb10/)
- [Inside look at modern web browser - Mariko Kosaka](https://developers.google.com/web/updates/2018/09/inside-browser-part1)
- [Regex Tester](https://extendsclass.com/regex-tester.html)
- [Chromium User Agent CSS](https://chromium.googlesource.com/chromium/src/third_party/+/master/blink/renderer/core/html/resources/html.css)
- [Firefox User Agent CSS](https://searchfox.org/mozilla-central/source/layout/style/res/html.css)
- [WebKit User Agent CSS](https://trac.webkit.org/browser/trunk/Source/WebCore/css/html.css)
- [W3 CSS2 Box Model](https://www.w3.org/TR/CSS22/box.html)