from geopy.geocoders import Nominatim
from overpy import Overpass
import math
import folium

# Initialize geocoder and Overpass API
geolocator = Nominatim(user_agent="berlin_poi_finder")
overpass = Overpass()

def get_coordinates(address):
    """Convert an address to latitude and longitude."""
    try:
        location = geolocator.geocode(address + ", Berlin, Germany")
        if location:
            return location.latitude, location.longitude
        else:
            raise ValueError("Address not found.")
    except Exception as e:
        print(f"Error geocoding address: {e}")
        return None, None

def haversine_distance(lat1, lon1, lat2, lon2):
    """Calculate the distance between two points in meters using the Haversine formula."""
    R = 6371000  # Earth's radius in meters
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)
    
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad
    
    a = math.sin(dlat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    distance = R * c
    return distance

def find_points_of_interest(lat, lon, radius=250):
    """Find named points of interest within a given radius from coordinates."""
    query = f"""
    [out:json];
    node(around:{radius},{lat},{lon})
    ["amenity"];
    out body;
    """
    
    try:
        result = overpass.query(query)
        pois = []
        
        for node in result.nodes:
            if "amenity" in node.tags:
                poi_lat = float(node.lat)
                poi_lon = float(node.lon)
                distance = haversine_distance(lat, lon, poi_lat, poi_lon)
                
                if distance <= radius:
                    poi_name = node.tags.get("name", "Unnamed POI")
                    if poi_name != "Unnamed POI":
                        poi_type = node.tags["amenity"]
                        pois.append({
                            "name": poi_name,
                            "type": poi_type,
                            "latitude": poi_lat,
                            "longitude": poi_lon,
                            "distance_m": round(distance, 2)
                        })
        return pois
    except Exception as e:
        print(f"Error querying Overpass API: {e}")
        return []

def create_map(lat, lon, pois, address):
    """Create a map with the address and POIs marked."""
    # Create a map centered on the input address
    m = folium.Map(location=[lat, lon], zoom_start=17)
    
    # Add a marker for the input address
    folium.Marker(
        [lat, lon],
        popup=f"Starting Point: {address}",
        icon=folium.Icon(color="red", icon="info-sign")
    ).add_to(m)
    
    # Add markers for each POI
    for poi in pois:
        folium.Marker(
            [poi["latitude"], poi["longitude"]],
            popup=f"{poi['name']} ({poi['type']})\n{poi['distance_m']}m",
            icon=folium.Icon(color="blue", icon="star")
        ).add_to(m)
    
    # Add a circle to show the 250m radius
    folium.Circle(
        location=[lat, lon],
        radius=250,
        color="green",
        fill=True,
        fill_opacity=0.1
    ).add_to(m)
    
    # Save the map to an HTML file
    m.save("poi_map.html")
    print("Map saved as 'poi_map.html'. Open it in a web browser to view.")

def main():
    # Input address
    address = input("Enter an address in Berlin: ")
    
    # Get coordinates
    lat, lon = get_coordinates(address)
    if lat is None or lon is None:
        print("Could not find coordinates for the address.")
        return
    
    print(f"Coordinates for {address}: ({lat}, {lon})")
    
    # Find POIs
    pois = find_points_of_interest(lat, lon, radius=250)
    
    # Display results
    if pois:
        print(f"\nFound {len(pois)} named points of interest within 250 meters:")
        for poi in pois:
            print(f"- {poi['name']} ({poi['type']}) at ({poi['latitude']}, {poi['longitude']}), "
                  f"{poi['distance_m']} meters away")
    else:
        print("No named points of interest found within 250 meters.")
        return
    
    # Create and save the map
    create_map(lat, lon, pois, address)

if __name__ == "__main__":
    main()