#!/usr/bin/env python3

import re
import svgwrite
import sys

k_blank = '#00FF00'


class Util:
    def _stripQuotes(line):
        return line[line.find('"')+1:line.rfind('"')]


class XpmLoader:
    def __init__(self, fname):
        self.colormap = {}
        self.pixelmap = []
        with open(fname, 'rt') as f:
            self.width, self.height, numcol, cwidth = self.load_values(f)
            self.load_colormap(f, numcol, cwidth)
            self.load_pixelmap(f, cwidth)

    def load_values(self, f):
        while True:
            line = f.readline()
            if line[0] != '"':
                continue
            line = Util._stripQuotes(line)
            return tuple([int(x) for x in line.split(' ')])
    
    def load_colormap(self, f, numcol, cwidth):
        for i in range(numcol):
            line = Util._stripQuotes(f.readline())
            char = line[:cwidth]
            if re.search(r'c None', line):
                continue
            color = re.search(r'c (#......)', line).group(1)
            self.colormap[char] = color
    
    def load_pixelmap(self, f, cwidth):
        for i in range(self.height):
            line = Util._stripQuotes(f.readline())
            row = [line[cwidth*j : cwidth*(j+1)] for j in range(self.width)]
            self.pixelmap += [row]


class LegoSvgPutter:
    def __init__(self, width, height):
        self.dwg = svgwrite.Drawing('out.svg', profile='tiny')
    
    def put_block(self, x, y, width, pins, color):
        hsize = 45
        vsize = 45
        pin_hsize = 25
        pin_vsize = 7
        pin_xoff = 10
        pin_yoff = -7

        left = x * hsize
        top = y * vsize

        if color == '#000000':
            stroke = '#666666'
        else:
            stroke = '#000000'

        self.dwg.add(self.dwg.rect((left, top), (width * hsize, vsize), stroke=stroke, fill=color))

        for i in range(width):
            if not pins[i]:
                continue
            self.dwg.add(
                self.dwg.rect(
                    (left + i*hsize + pin_xoff, top + pin_yoff),
                    (pin_hsize, pin_vsize),
                    stroke=stroke,
                    fill=color
                )
            )

    def save(self):
        self.dwg.save()


def make_block(pixmap, column, row, length, color):
    left = column - length
    if row == 0:
        pins = [1] * length
    else:
        pins = [[0,1][pixmap.colormap[pixmap.pixelmap[row-1][x]] == k_blank] for x in range(left, left+length)]
    return (left, row, length, pins, color)


def blockize(pixmap):
    for row in range(pixmap.height):
        color = None
        length = 0
        for column in range(pixmap.width):
            c = pixmap.colormap[pixmap.pixelmap[row][column]]
            if color is not None and (c == k_blank or c != color or length == 4):
                yield make_block(pixmap, column, row, length, color)
                length = 0

            if c != k_blank:
                color = c
                length += 1
            else:
                color = None
                length = 0
        
        if length > 0:
            yield make_block(pixmap, pixmap.width, row, length, color)


def main():
    if len(sys.argv) < 2 or sys.argv[1] == '-h':
        print('Usage: {} <input.xpm>'.format(sys.argv[0]), file=sys.stderr)
        return 1
    pixmap = XpmLoader(sys.argv[1])
    
    out = LegoSvgPutter(pixmap.width, pixmap.height)
    for block in blockize(pixmap):
        out.put_block(*block)
    out.save()

    return 0

if __name__ == '__main__':
    sys.exit(main())
