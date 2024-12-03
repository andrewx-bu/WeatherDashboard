# Helper functions

def convert_wind_deg_to_direction(deg: float) -> str:
    """
    Converts wind degree (0 to 360) to cardinal direction.

    Args:
        deg (float): Wind direction in degrees (0 to 360).

    Returns:
        str: Corresponding cardinal direction (N, NE, E, SE, S, SW, W, NW).
        (Defaults to '?')
    """
    if deg >= 337.5 or deg < 22.5:
        return "N"
    elif 22.5 <= deg < 67.5:
        return "NE"
    elif 67.5 <= deg < 112.5:
        return "E"
    elif 112.5 <= deg < 157.5:
        return "SE"
    elif 157.5 <= deg < 202.5:
        return "S"
    elif 202.5 <= deg < 247.5:
        return "SW"
    elif 247.5 <= deg < 292.5:
        return "W"
    elif 292.5 <= deg < 337.5:
        return "NW"
    else:
        return "?"