DISPLAY_SPEC = {
    'static': {
        'key': 'static',
        'name': 'Static',
        'description': "Static displays, like e-ink, that cannot display animation",
    },
    'dynamic': {
        'key': 'dynamic',
        'name': 'Dynamic',
        'description': "Displays like LCDs that can display a GIF animation",
    },
    'browser': {
        'key': 'browser',
        'name': 'Browser',
        'description': "Browser displays that can render HTML and CSS",
    },
}

COLOR_SPEC = {
    '1b': {
        'key': '1b',
        'name': 'Monochrome',
        'description': "Monochromatic e-ink or OLED displays",
    },
    '3b': {
        'key': '3b',
        'name': '3-bit color (8 colors)',
        'description': "3-bit color supporting 8 colors",
    },
    '3b7': {
        'key': '3b7',
        'name': '3-bit color (7 colors)',
        'description': "3-bit color supporting 7 colors",
    },
    '16b': {
        'key': '16b',
        'name': '16-bit color',
        'description': "16-bit full color",
    },
    'full': {
        'key': 'full',
        'name': 'Full Color',
        'description': "Full color (24-32 bit)",
    },
}