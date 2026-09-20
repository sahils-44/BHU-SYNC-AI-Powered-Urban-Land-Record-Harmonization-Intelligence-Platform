from math import radians, sin, cos, sqrt, atan2


def calculate_distance(
    lat1,
    lon1,
    lat2,
    lon2
):
    """
    Calculate approximate distance between
    two latitude/longitude points in meters.
    """

    if any(
        value is None
        for value in [lat1, lon1, lat2, lon2]
    ):
        return None

    R = 6371000  # Earth radius in meters

    lat1 = radians(lat1)
    lat2 = radians(lat2)

    delta_lat = radians(lat2 - lat1)
    delta_lon = radians(lon2 - lon1)

    a = (
        sin(delta_lat / 2) ** 2
        +
        cos(lat1)
        * cos(lat2)
        * sin(delta_lon / 2) ** 2
    )

    c = 2 * atan2(
        sqrt(a),
        sqrt(1 - a)
    )

    return R * c


def spatial_match_score(distance):

    if distance is None:
        return 0

    if distance <= 20:
        return 25

    elif distance <= 50:
        return 15

    elif distance <= 100:
        return 5

    return 0