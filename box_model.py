class BoxModel:
    def __init__(self):
        # width and height available for it's content (ie children)
        # however note it may overflow
        self.content_width = 0
        self.content_height = 0

        # box model properties
        self.margin_top = 0
        self.margin_right = 0
        self.margin_bottom = 0
        self.margin_left = 0

        self.padding_top = 0
        self.padding_right = 0
        self.padding_bottom = 0
        self.padding_left = 0

        self.border_top = 0
        self.border_right = 0
        self.border_bottom = 0
        self.border_left = 0

        # the relative position of the element from it's parent's content box
        self.relative_left = 0
        self.relative_top = 0

    @property
    def padding_width(self):
        return self.padding_left + self.padding_right

    @property
    def padding_height(self):
        return self.padding_top + self.padding_bottom

    @property
    def border_width(self):
        return self.border_left + self.border_right

    @property
    def border_height(self):
        return self.border_top + self.border_bottom

    @property
    def margin_width(self):
        return self.margin_left + self.margin_right

    @property
    def margin_height(self):
        return self.margin_top + self.margin_bottom

    @property
    def width(self):
        return self.border_width + self.padding_width + self.content_width

    @property
    def height(self):
        return self.border_height + self.padding_height + self.content_height

    @width.setter
    def width(self, width):  # content width cannot be negative
        self.content_width = max(width - self.border_width - self.padding_width, 0)

    @height.setter
    def height(self, height):  # content height cannot be negative
        self.content_height = max(height - self.border_height - self.padding_height, 0)

    @property
    def box_width(self):
        return self.content_width + self.padding_width + self.border_width + self.margin_width

    @property
    def box_height(self):
        return self.content_height + self.padding_height + self.border_height + self.margin_height

    @box_width.setter
    def box_width(self, box_width):
        self.content_width = max(box_width - self.padding_width - self.border_width - self.margin_width, 0)

    @box_height.setter
    def box_height(self, box_height):
        self.content_height = max(box_height - self.padding_height - self.border_height - self.margin_height, 0)

    def __str__(self):
        return f'BoxModel(content_size=({self.content_width, self.content_height}), ' \
            f'box_size=({self.box_width}, {self.box_height}))'
