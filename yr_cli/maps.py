import base64
import io
import sys

import PIL.ImageDraw
import staticmaps


def textsize(self: PIL.ImageDraw.ImageDraw, *args, **kwargs):
    x, y, w, h = self.textbbox((0, 0), *args, **kwargs)
    return w, h


# Monkeypatch fix for https://github.com/flopp/py-staticmaps/issues/39
PIL.ImageDraw.ImageDraw.textsize = textsize


def create_map_with_box(latitude, longitude, box_size_km=1, zoom=14):
    context = staticmaps.Context()
    context.set_tile_provider(staticmaps.tile_provider_OSM)
    center = staticmaps.create_latlng(latitude, longitude)
    box = staticmaps.Area(
        [
            staticmaps.create_latlng(
                latitude + box_size_km / 222, longitude - box_size_km / 222
            ),
            staticmaps.create_latlng(
                latitude + box_size_km / 222, longitude + box_size_km / 222
            ),
            staticmaps.create_latlng(
                latitude - box_size_km / 222, longitude + box_size_km / 222
            ),
            staticmaps.create_latlng(
                latitude - box_size_km / 222, longitude - box_size_km / 222
            ),
            staticmaps.create_latlng(
                latitude + box_size_km / 222, longitude - box_size_km / 222
            ),
        ],
        fill_color=staticmaps.TRANSPARENT,
        color=staticmaps.RED,
        width=2,
    )
    context.add_object(box)
    context.set_center(center)
    context.set_zoom(zoom)
    image = context.render_pillow(1000, 600)

    buffered = io.BytesIO()
    image.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue())
    image_bytes = (
        b"".join(
            [
                b"\033]",
                b"1337;File=inline=1",
                b":",
                img_str,
                b"\007",
            ]
        )
        + b"\n"
    )
    sys.stdout.buffer.write(image_bytes)
    sys.stdout.buffer.flush()
