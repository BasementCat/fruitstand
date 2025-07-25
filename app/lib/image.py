from typing import List

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


def convert_colors(color_spec: str, input_path: str):
    cs = COLOR_SPEC.get(color_spec, COLOR_SPEC['1b'])

    in_im = Image.open(input_path).convert('RGB')

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
        in_im = in_im.point(lambda p: 255 if p >= 128 else 0)
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
