from services.spatial_matcher import (
    calculate_distance,
    spatial_match_score
)


cadastral_lat = 19.8832
cadastral_lon = 74.4761

municipal_lat = 19.8833
municipal_lon = 74.4762


distance = calculate_distance(
    cadastral_lat,
    cadastral_lon,
    municipal_lat,
    municipal_lon
)


score = spatial_match_score(distance)


print("================================")
print("BHU-SYNC SPATIAL MATCH")
print("================================")

print(
    f"Distance: {distance:.2f} meters"
)

print(
    f"Spatial Score: {score}/25"
)