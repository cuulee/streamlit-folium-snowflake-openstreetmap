from typing import NamedTuple


class Coordinates(NamedTuple):
    x1: float
    y1: float
    x2: float
    y2: float

    @classmethod
    def from_dict(cls, coordinates: dict) -> "Coordinates":
        x1 = float(coordinates["_southWest"]["lng"])
        y1 = float(coordinates["_southWest"]["lat"])
        x2 = float(coordinates["_northEast"]["lng"])
        y2 = float(coordinates["_northEast"]["lat"])

        return cls(x1, y1, x2, y2)

    @classmethod
    def get_center(cls, map_data: dict = None):
        if map_data is None:
            return (39.8, -86.1)

        try:
            y1 = float(map_data["bounds"]["_southWest"]["lat"])
            y2 = float(map_data["bounds"]["_northEast"]["lat"])
            x1 = float(map_data["bounds"]["_southWest"]["lng"])
            x2 = float(map_data["bounds"]["_northEast"]["lng"])

            return ((y2 + y1) / 2, (x2 + x1) / 2)
        except (KeyError, TypeError):
            return (39.8, -86.1)
