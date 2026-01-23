from typing import List, Tuple, Optional

from PIL import Image

from app.constants import COLOR_SPEC


def convert_palette(palette: List[int]) -> List[int]:
    """\
    Convert a palette of 24 bit integers to Pillow's palette format of
    individual color channels [r1, g1, b1, r2, g2, b2, ...]
    """

    out = []
    for c in palette:
        out.append(c >> 16 & 0xff)
        out.append(c >> 8 & 0xff)
        out.append(c & 0xff)
    return out


def convert_colors__cs(color_spec: str, in_im):
    """Initial conversion to what's specified in color_spec"""
    cs = COLOR_SPEC.get(color_spec, COLOR_SPEC['1b'])

    if cs['bits'] == 1:
        mode = '1'
    elif cs['bits'] < 16:
        mode = 'P'
    else:
        # Even for 16b, pillow doesn't support rgb565 - just use rgb and let the client handle it...
        mode = 'RGB'

    out_im = Image.new(mode, in_im.size)
    if cs['palette'] and cs['bits'] < 16 and cs['bits'] > 1:
        out_im.putpalette(convert_palette(cs['palette']))

    if cs['bits'] == 1:
        in_im = in_im.convert('L')
        in_im = in_im.point(lambda p: 255 if p >= 170 else 0)
        out_im.paste(in_im, tuple([0, 0] + list(in_im.size)))
    elif cs['bits'] < 16:
        in_im = in_im.quantize(
            colors=len(cs['palette'] or []) or 2 ** cs['bits'],
            palette=out_im if cs['palette'] else None,
            dither=Image.Dither.FLOYDSTEINBERG,
        )
        out_im.paste(in_im, tuple([0, 0] + list(in_im.size)))
    else:
        in_im = in_im.convert(mode, dither=None, palette=out_im.palette)
        out_im.paste(in_im, tuple([0, 0] + list(in_im.size)))

    return out_im


def convert_colors__bits(bit_depth: Optional[int], in_im):
    """Second conversion to actual bit depth"""
    if bit_depth:
        if bit_depth >= 16:
            return in_im.convert('RGB')
        else:
            # must be 1, 16, 24 - this case would be 1 bit
            out_im = Image.new('1', in_im.size)
            in_im = in_im.convert('L')
            in_im = in_im.point(lambda p: 255 if p >= 170 else 0)
            out_im.paste(in_im, tuple([0, 0] + list(in_im.size)))
            return out_im
    return in_im


def convert_colors(bit_depth: Optional[int], color_spec: str, input_path: str):
    im = Image.open(input_path).convert('RGB')
    im = convert_colors__cs(color_spec, im)
    im = convert_colors__bits(bit_depth, im)
    return im
