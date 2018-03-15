# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2018, Galen Curwen-McAdams

import uuid
import attr
import colour

@attr.s
class Rule(object):
    source_field = attr.ib(default="")
    comparator_symbol = attr.ib(default="")
    comparator_params = attr.ib(default=attr.Factory(list))
    dest_field = attr.ib(default="")
    rule_result = attr.ib(default="")
    rough_amount = attr.ib(default=0)

    def quote(self, string):
        if string:
            if not string.startswith('"'):
                string = '"' + string
            if not string.endswith('"'):
                string += '"'
            return string
        else:
            return '""'
    @property
    def rule_result_string(self):
        quoted_rule_result = self.rule_result
        return self.quote(quoted_rule_result)

    @property
    def comparator_params_string(self):
        params = self.comparator_params
        if self.comparator_symbol == "~~":
            params[0] = self.quote(params[0])
        return " ".join(params)

    @property
    def as_string(self):
        s = attr.asdict(self)
        s.update({'comparator_params_string' : self.comparator_params_string})
        s.update({'rule_result_string' : self.rule_result_string})
        return "{source_field} {comparator_symbol} {comparator_params_string} -> {dest_field} {rule_result_string}".format(**s)

@attr.s
class RuleSet(object):
    rules = attr.ib(default=attr.Factory(list))

    @property
    def as_string(self):
        return ""

@attr.s
class RuleSymbols(object):
    symbols = {
    "~~" : "case insensitive equals",
    "is" : "is of type",
    "between" : "integer range between"
    }

    types = ["int", "roman", "str"]

    # symbol_params
    # is <type>
    # between int1,int2

@attr.s
class Group(object):
    regions = attr.ib(default=attr.Factory(list))
    color = attr.ib(default=None)
    name = attr.ib(default="")
    hide = attr.ib(default=False)
    source_dimensions = attr.ib(default=attr.Factory(list))
    source = attr.ib(default="")

    @color.validator
    def check(self, attribute, value):
        if value is None:
            setattr(self,'color', colour.Color(pick_for=self))

    @property
    def x(self):
        return self.region_rectangle()[0]

    @property
    def x2(self):
        return self.region_rectangle()[2]

    @property
    def y(self):
        return self.region_rectangle()[1]

    @property
    def y2(self):
        return self.region_rectangle()[3]

    @property
    def width(self):
        return self.x2 - self.x

    @property
    def height(self):
        return self.y2 - self.y
    
    @property
    def scaled_bounding_rectangle(self):
        # scaled to fullsize with offsets removed
        # and coordinates shifted to upper left 0,0
        # Problem: final y axis of rectangle is a little off
        try:
            rect = self.region_rectangle()
            ox = self.display_offset_x
            oy = self.display_offset_y
            # remove offsets
            print("offsets x, y", self.display_offset_x, self.display_offset_y)
            rect = [rect[0] - ox, rect[1], rect[2] - ox, rect[3]]
            # get xy scaling
            x_scale = self.source_width / self.source_dimensions[0]
            y_scale = self.source_height / self.source_dimensions[1]
            x = rect[0]
            y = rect[1]
            x2 = rect[2]
            y2 = rect[3]
            # kivy canvas 0,0 is lower left corner
            # image processing expects 0,0 is upper left corner
            x = int(round(x * x_scale))
            y = int(round(y * y_scale))
            x2 = int(round(x2 * x_scale))
            y2 = int(round(y2 * y_scale))
            # subtract height to go from bottom left 0,0
            # used by kivy canvas to top left 0,0 used by
            # pillow, x does not need adjustment
            h = abs(y2 - y)
            y -= self.source_height
            y2 -= self.source_height
            y = abs(y)
            y2 = abs(y2)
            # get width and height to print xywh
            # use with 'ma-cli image' rectangle command
            # to debug coordinates
            w = abs(x2 - x)
            h = abs(y2 - y)
            print("scaled rect:", x,y,x2,y2)
            print("scaled xywh:", x, y, w, h)
            return [x, y, x2, y2]
        except TypeError:
            return None

    @property
    def scaled_width(self):
        pass

    @property
    def scaled_height(self):
        pass

    @property
    def bounding_rectangle(self):
        #x y w h
        rect = self.region_rectangle()
        try:
            rect[2] = rect[2] - rect[0]
            rect[3] = rect[3] - rect[1]
            return rect
        except TypeError:
            return None

    def bounding_contains_point(self, x, y):
        contains_x = False
        contains_y = False
        rect = self.region_rectangle()
        try:
            if rect[0] < x < rect[2]:
                contains_x = True

            if rect[1] < y <rect[3]:
                contains_y = True
        except TypeError:
            pass

        if contains_x and contains_y:
            return True
        else:
            return False

    def region_rectangle(self):
        """Return bounding rectangle of
        all regions"""
        min_x = None
        min_y = None
        max_x = None
        max_y = None

        for region in self.regions:
            if min_x is None or region[0] < min_x:
                min_x = region[0]

            if min_y is None or region[1] < min_y:
                min_y = region[1]

            if max_x is None or region[2] > max_x:
                max_x = region[2]

            if max_y is None or region[3] > max_y:
                max_y = region[3]

        return [min_x, min_y, max_x, max_y]

@attr.s
class Category(object):
    color = attr.ib(default=None)
    name = attr.ib(default=None)
    rough_amount = attr.ib(default=0)
    rough_amount_start = attr.ib(default=None)
    rough_amount_end = attr.ib(default=None)
    # rough_order could be negative float
    rough_order = attr.ib(default=None)
    # set name to random uuid if none supplied
    @name.validator
    def check(self, attribute, value):
        if value is None:
            setattr(self,'name',str(uuid.uuid4()))
