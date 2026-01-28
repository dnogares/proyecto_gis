
import geopandas as gpd
from shapely.geometry import Point, Polygon
import os

# Create a small GeoDataFrame
data = {
    'name': ['Punto 1', 'Punto 2', 'Parcela 1'],
    'geometry': [
        Point(-3.70379, 40.41678), # Madrid
        Point(-3.70379, 40.41680),
        Polygon([(-3.704, 40.416), (-3.703, 40.416), (-3.703, 40.417), (-3.704, 40.417)])
    ]
}
gdf = gpd.GeoDataFrame(data, crs="EPSG:4326") # WGS84

# Ensure directory exists
os.makedirs('capas/fgb', exist_ok=True)

# Save as FlatGeobuf
gdf.to_file('capas/fgb/test_capa.fgb', driver='FlatGeobuf')
print("✅ Created capas/fgb/test_capa.fgb")
