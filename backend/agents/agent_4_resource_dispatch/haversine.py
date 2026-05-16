from math import radians, cos, sin, asin, sqrt

def haversine(lat1, lng1, lat2, lng2):
    """
    Calculate distance in km between two lat/lng points.
    """
    R = 6371
    dlat = radians(lat2 - lat1)
    dlng = radians(lng2 - lng1)
    a = sin(dlat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlng/2)**2
    return round(2 * R * asin(sqrt(a)), 2)

if __name__ == "__main__":
    # Test: F-8 Rescue Station to G-10 crisis center
    dist = haversine(33.7080, 73.0479, 33.6844, 73.0479)
    print(f"F-8 to G-10: {dist} km")
