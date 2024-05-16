#!/usr/bin/env python3

import json
import os
import shutil
import sys
from math import cos, pi
from pathlib import Path
from subprocess import Popen, PIPE
from time import strftime
from zipfile import ZipFile

from qgis.core import QgsApplication, QgsCoordinateReferenceSystem, QgsCoordinateTransform, QgsProject


def time_str():
    return strftime('%H:%M:%S')


def overpass_query(output_dir, name, query):
    print(f"{time_str()} Generating {name}.geojson...")
    full_query = f"[out:json][bbox:{','.join(str(x) for x in bbox)}];({query});out body;>;out skel qt;"
    with (output_dir / f"{name}.geojson").open("w+") as f:
        curl = Popen(["curl", "-fsSL", "http://overpass-api.de/api/interpreter", "-d", full_query], stdout=PIPE)
        osmtogeojson = Popen(["osmtogeojson"], stdin=curl.stdout, stdout=f)
        curl.stdout.close()
        osmtogeojson.communicate()


generate_input  = 1
generate_output = 1
generate_tiles  = 1

this_dir = Path(__file__).parent

try:
    config = json.loads((this_dir / "config.json").read_text())
except:
    config = {}

if len(sys.argv) != 2 or sys.argv[1] in ("-h", "--help"):
    location_hint = next(iter(list(config.get("locations", {}).keys())), None)
    if location_hint is not None:
        location_hint = f" (e.g. '{location_hint}')"
    print(f"Usage: {sys.argv[0]} LOCATION")
    print()
    print("Possible LOCATION values (from config.json file):")
    locations = list(config.get("locations", {}).keys())
    if locations:
        locations = '\n  * '.join(sorted(locations))
        print(f"  * {locations}")
    else:
        print("  (no locations defined, please edit the file to add some)")
    sys.exit(1 if len(sys.argv) != 2 else 0)

location = sys.argv[1]
location_config = config["locations"][location]

bbox = location_config["bbox"]
assert bbox[0] < bbox[2]
assert bbox[1] < bbox[3]

srk_mapstyle_dir = this_dir / "strassenraumkarte-neukoelln" / "mapstyle"
srk_geojson_dir = srk_mapstyle_dir / "layer" / "geojson"

sp_dir = this_dir / "street_parking.py"
sp_data_dir = sp_dir / "data"

tw_dir = this_dir / "tile_writer"

output_dir = this_dir / "output" / location

crs_to = location_config["crs"]

os.environ["OSM_STRASSENRAUMKARTE_PROC_CROSSINGS"]       = "1"
os.environ["OSM_STRASSENRAUMKARTE_PROC_CR_MARKINGS"]     = "1"
os.environ["OSM_STRASSENRAUMKARTE_PROC_CR_LINES"]        = "1"
os.environ["OSM_STRASSENRAUMKARTE_PROC_CR_TACTILE_PAV"]  = "1"
os.environ["OSM_STRASSENRAUMKARTE_PROC_LANE_MARKINGS"]   = "1"
os.environ["OSM_STRASSENRAUMKARTE_PROC_HIGHWAY_BACKUP"]  = "1"
os.environ["OSM_STRASSENRAUMKARTE_PROC_SERVICE"]         = "1"
os.environ["OSM_STRASSENRAUMKARTE_PROC_ONEWAYS"]         = "1"
os.environ["OSM_STRASSENRAUMKARTE_PROC_TRAFFIC_CALMING"] = "1"
os.environ["OSM_STRASSENRAUMKARTE_PROC_CYCLEWAYS"]       = "1"
os.environ["OSM_STRASSENRAUMKARTE_PROC_PATH_AREAS"]      = "1"
os.environ["OSM_STRASSENRAUMKARTE_PROC_RAILWAYS"]        = "1"
os.environ["OSM_STRASSENRAUMKARTE_PROC_BUILDINGS"]       = "1"
os.environ["OSM_STRASSENRAUMKARTE_PROC_HOUSENUMBERS"]    = "1"
os.environ["OSM_STRASSENRAUMKARTE_PROC_WATER_BODY"]      = "1"
os.environ["OSM_STRASSENRAUMKARTE_PROC_LANDCOVER"]       = "1"
os.environ["OSM_STRASSENRAUMKARTE_PROC_PITCHES"]         = "1"
os.environ["OSM_STRASSENRAUMKARTE_PROC_PLAYGR_LANDUSE"]  = "1"
os.environ["OSM_STRASSENRAUMKARTE_PROC_PLAYGR_EQUIP"]    = "1"
os.environ["OSM_STRASSENRAUMKARTE_PROC_ORIENT_MAN_MADE"] = "1"
os.environ["OSM_STRASSENRAUMKARTE_PROC_TREES"]           = "1"
os.environ["OSM_STRASSENRAUMKARTE_PROC_FORESTS"]         = "1"
os.environ["OSM_STRASSENRAUMKARTE_PROC_CARS"]            = "1"
os.environ["OSM_STRASSENRAUMKARTE_PROC_LABELS"]          = "1"
os.environ["OSM_STRASSENRAUMKARTE_PROC_PARKING_AREAS"]   = "1"
os.environ["OSM_STRASSENRAUMKARTE_PROC_PROTECTED_BL"]    = "1"

os.environ["OSM_TILE_WRITER_START_Z"]                    = "15"
os.environ["OSM_TILE_WRITER_END_Z"]                      = "21"
os.environ["OSM_TILE_WRITER_STEP"]                       = "32"
os.environ["OSM_TILE_WRITER_IMAGE_FORMAT"]               = "jpg"

os.environ.update({f"OSM_{k}": v for k, v in location_config.get("settings", {}).items()})

os.environ["OSM_STRASSENRAUMKARTE_CRS_TO"]               = crs_to
os.environ["OSM_STREET_PARKING_CRS_TO"]                  = crs_to
os.environ["OSM_TILE_WRITER_OUTPUT_PATH"]                = str(output_dir / "tiles")
os.environ["OSM_TILE_WRITER_AREA_OF_INTEREST"]           = str(srk_geojson_dir / "map_extent" / "map_extent.geojson")

# Initialize QGIS Application
app = QgsApplication([], True)
QgsApplication.initQgis()

if generate_input:
    print(f"{time_str()} ===== Input =====")

    ct = QgsCoordinateTransform(QgsCoordinateReferenceSystem("EPSG:4326"), QgsCoordinateReferenceSystem("EPSG:3857"), QgsProject.instance())
    bbox_3857 = list(ct.transform(bbox[1], bbox[0])) + list(ct.transform(bbox[3], bbox[2]))

    print(f"{time_str()} Generating map_extent.geojson...")
    (srk_geojson_dir / "map_extent" / "map_extent.geojson").write_text(json.dumps({
      "type": "FeatureCollection",
      "name": "map_extend",
      "crs": {
        "type": "name",
        "properties": {
          "name": "urn:ogc:def:crs:EPSG::3857",
        },
      },
      "features": [
        {
          "type": "Feature",
          "properties": {},
          "geometry": {
            "type": "MultiPolygon",
            "coordinates": [
              [
                [
                  [bbox_3857[0], bbox_3857[3]],
                  [bbox_3857[2], bbox_3857[3]],
                  [bbox_3857[2], bbox_3857[1]],
                  [bbox_3857[0], bbox_3857[1]],
                  [bbox_3857[0], bbox_3857[3]],
                ],
              ],
            ],
          },
        },
      ],
    }))

    print(f"{time_str()} Generating map_fog_square.geojson...")
    (srk_geojson_dir / "fog" / "map_fog_square.geojson").write_text(json.dumps({
      "type": "FeatureCollection",
      "name": "map_fog_square",
      "crs": {
        "type": "name",
        "properties": {
          "name": "urn:ogc:def:crs:EPSG::3857",
        },
      },
      "features": [
        {
          "type": "Feature",
          "properties": {},
          "geometry": {
            "type": "MultiPolygon",
            "coordinates": [
              [
                [
                  [bbox_3857[0] - 10000, bbox_3857[3] + 10000],
                  [bbox_3857[2] + 10000, bbox_3857[3] + 10000],
                  [bbox_3857[2] + 10000, bbox_3857[1] - 10000],
                  [bbox_3857[0] - 10000, bbox_3857[1] - 10000],
                  [bbox_3857[0] - 10000, bbox_3857[3] + 10000],
                ],
                [
                  [bbox_3857[0], bbox_3857[3]],
                  [bbox_3857[0], bbox_3857[1]],
                  [bbox_3857[2], bbox_3857[1]],
                  [bbox_3857[2], bbox_3857[3]],
                  [bbox_3857[0], bbox_3857[3]],
                ],
              ],
            ],
          },
        },
      ],
    }))

    overpass_query(srk_geojson_dir, "amenity", """
      nwr["amenity"];
      nwr["disused:amenity"];
    """)

    overpass_query(srk_geojson_dir, "area_highway", """
      nwr["area:highway"];
      nwr["road_marking"];
      nwr["road_marking:forward"];
      nwr["road_marking:backward"];
      nwr["road_marking:left"];
      nwr["road_marking:right"];
    """)

    overpass_query(srk_geojson_dir, "barriers", """
      nwr["barrier"]["location"!="underground"]["level"!="-1"]["level"!="-2"]["level"!="-3"];
    """)

    overpass_query(srk_geojson_dir, "bridge", """
      way["man_made"="bridge"];
      relation["man_made"="bridge"];
    """)

    overpass_query(srk_geojson_dir, "building_part", """
      way["building:part"]["location"!="underground"]["level"!="-1"]["level"!="-2"]["level"!="-3"];
    """)

    overpass_query(srk_geojson_dir, "buildings", """
      nwr["building"]["location"!="underground"]["level"!="-1"]["level"!="-2"]["level"!="-3"];
    """)

    overpass_query(srk_geojson_dir, "entrance", """
      node["entrance"];
      node["entrance_marker:subway"];
      node["entrance_marker:s-train"];
    """)

    overpass_query(srk_geojson_dir, "highway", """
      // streets
      way["highway"="primary"];
      way["highway"="primary_link"];
      way["highway"="secondary"];
      way["highway"="secondary_link"];
      way["highway"="tertiary"];
      way["highway"="tertiary_link"];
      way["highway"="residential"];
      way["highway"="unclassified"];
      way["highway"="living_street"];
      way["highway"="pedestrian"];
      way["highway"="road"];
      way["highway"="service"];
      way["highway"="track"];
      way["highway"="bus_guideway"];

      // streets under construction
      way["highway"="construction"]["construction"="primary"];
      way["highway"="construction"]["construction"="primary_link"];
      way["highway"="construction"]["construction"="secondary"];
      way["highway"="construction"]["construction"="secondary_link"];
      way["highway"="construction"]["construction"="tertiary"];
      way["highway"="construction"]["construction"="tertiary_link"];
      way["highway"="construction"]["construction"="residential"];
      way["highway"="construction"]["construction"="unclassified"];
      way["highway"="construction"]["construction"="living_street"];
      way["highway"="construction"]["construction"="pedestrian"];
      way["highway"="construction"]["construction"="road"];
      way["highway"="construction"]["construction"="service"];
      way["highway"="construction"]["construction"="track"];
      way["highway"="construction"]["construction"="bus_guideway"];

      // bus stops
      way["highway"="platform"];
      way["public_transport"="platform"];
      node["highway"="bus_stop"];

      // crossings and traffic signals
      node["highway"="traffic_signals"];
      node["highway"="crossing"];
      node["highway"="stop"];
      node["highway"="give_way"];
      node["kerb"];

      // traffic calming
      nwr["traffic_calming"];
    """)

    overpass_query(srk_geojson_dir, "housenumber", """
      nwr["addr:housenumber"][!"name"][!"disused:name"][!"amenity"][!"shop"][!"disused:amenity"][!"disused:shop"][!"healthcare"][!"office"][!"leisure"][!"craft"];
    """)

    overpass_query(srk_geojson_dir, "landuse", """
      way["landuse"];
      relation["landuse"];
      way["landcover"];
      relation["landcover"];
    """)

    overpass_query(srk_geojson_dir, "leisure", """
      nwr["leisure"];
    """)

    overpass_query(srk_geojson_dir, "man_made", """
      nwr["man_made"="water_well"];
      nwr["man_made"="monitoring_station"];
      nwr["man_made"="mast"];
      nwr["man_made"="pole"];
      nwr["man_made"="flagpole"];
      nwr["man_made"="chimney"];
      nwr["man_made"="street_cabinet"];
      nwr["man_made"="manhole"];
      nwr["man_made"="planter"];
      nwr["man_made"="guard_stone"];

      nwr["man_made"="embankment"];

      nwr["highway"="street_lamp"];
      nwr["highway"="traffic_sign"];

      nwr["advertising"];

      nwr["emergency"="fire_hydrant"];

      nwr["tourism"="artwork"];
      nwr["tourism"="information"];

      nwr["historic"="memorial"];

      nwr["amenity"="loading_ramp"];
      nwr["amenity"="vending_machine"]["vending"="parking_tickets"];
    """)

    overpass_query(srk_geojson_dir, "motorway", """
      way["highway"="motorway"];
      way["highway"="trunk"];
      way["highway"="motorway_link"];
      way["highway"="trunk_link"];
    """)

    overpass_query(srk_geojson_dir, "natural", """
      nwr["natural"];
    """)

    overpass_query(srk_geojson_dir, "path", """
      way["highway"="path"];
      way["highway"="footway"];
      way["highway"="steps"];
      way["highway"="cycleway"];

      way["highway"="track"];
    """)

    overpass_query(srk_geojson_dir, "place", """
      nwr["place"];
    """)

    overpass_query(srk_geojson_dir, "playground", """
      nwr["playground"];
      nwr["skatepark:obstacles"];
    """)

    overpass_query(srk_geojson_dir, "railway", """
      nwr["railway"];
    """)

    overpass_query(srk_geojson_dir, "routes", """
      relation["route"="bicycle"];
    """)

    overpass_query(srk_geojson_dir, "waterway", """
      way["waterway"];
    """)

    overpass_query(sp_data_dir, "input", """
      // streets
      way["highway"="primary"];
      way["highway"="primary_link"];
      way["highway"="secondary"];
      way["highway"="secondary_link"];
      way["highway"="tertiary"];
      way["highway"="tertiary_link"];
      way["highway"="residential"];
      way["highway"="unclassified"];
      way["highway"="living_street"];
      way["highway"="pedestrian"];
      way["highway"="road"];
      way["highway"="service"];
      way["highway"="track"];
      way["highway"="bus_guideway"];

      // streets under construction
      way["highway"="construction"]["construction"="primary"];
      way["highway"="construction"]["construction"="primary_link"];
      way["highway"="construction"]["construction"="secondary"];
      way["highway"="construction"]["construction"="secondary_link"];
      way["highway"="construction"]["construction"="tertiary"];
      way["highway"="construction"]["construction"="tertiary_link"];
      way["highway"="construction"]["construction"="residential"];
      way["highway"="construction"]["construction"="unclassified"];
      way["highway"="construction"]["construction"="living_street"];
      way["highway"="construction"]["construction"="pedestrian"];
      way["highway"="construction"]["construction"="road"];
      way["highway"="construction"]["construction"="service"];
      way["highway"="construction"]["construction"="track"];
      way["highway"="construction"]["construction"="bus_guideway"];

      // (foot)ways and path that can be used by motor vehicles
      way["highway"]["motor_vehicle"]["motor_vehicle"!="no"];
      way["highway"]["vehicle"]["vehicle"!="no"]["motor_vehicle"!="no"];
      way["highway"]["emergency"]["emergency"!="no"];

      // separately mapped street/street side parking
      nwr["amenity"="parking"]["parking"="street_side"];
      nwr["amenity"="parking"]["parking"="lane"];
      nwr["amenity"="parking"]["parking"="on_kerb"];
      nwr["amenity"="parking"]["parking"="half_on_kerb"];
      nwr["amenity"="parking"]["parking"="shoulder"];

      // traffic signals, crossings, bus stops, turning loops (affecting street parking)
      node["highway"="traffic_signals"];
      node["highway"="crossing"];
      node["highway"="stop"];
      node["highway"="give_way"];
      node["highway"="bus_stop"];
      node["highway"="turning_circle"];
      node["highway"="turning_loop"];

      // installations and obstacles on parking lanes
      nwr["obstacle:parking"="yes"];
      nwr["amenity"="bicycle_parking"]["bicycle_parking:position"="lane"];
      nwr["amenity"="bicycle_parking"]["bicycle_parking:position"="street_side"];
      nwr["amenity"="bicycle_parking"]["bicycle_parking:position"="kerb_extension"];
      nwr["amenity"="motorcycle_parking"]["parking"="lane"];
      nwr["amenity"="motorcycle_parking"]["parking"="street_side"];
      nwr["amenity"="motorcycle_parking"]["parking"="kerb_extension"];
      nwr["amenity"="small_electric_vehicle_parking"]["small_electric_vehicle_parking:position"="lane"];
      nwr["amenity"="small_electric_vehicle_parking"]["small_electric_vehicle_parking:position"="street_side"];
      nwr["amenity"="small_electric_vehicle_parking"]["small_electric_vehicle_parking:position"="kerb_extension"];
      nwr["amenity"="bicycle_rental"]["bicycle_rental:position"="lane"];
      nwr["amenity"="bicycle_rental"]["bicycle_rental:position"="street_side"];
      nwr["amenity"="bicycle_rental"]["bicycle_rental:position"="kerb_extension"];
      nwr["leisure"="parklet"];
      nwr["amenity"="loading_ramp"];
      nwr["leisure"="outdoor_seating"]["outdoor_seating"="parklet"];
      way["traffic_calming"="kerb_extension"];
      way["area:highway"="prohibited"];
    """)


if generate_output or generate_tiles:
    sys.path.append(str(Path(app.pkgDataPath()) / "python" / "plugins"))

if generate_output:
    sys.path.append(str(srk_mapstyle_dir))
    sys.path.append(str(sp_dir))

    print(f"{time_str()} ===== Output =====")

    scale_factor = 1 / cos((bbox[0] + bbox[2]) / 2 * pi / 180)
    with ZipFile(srk_mapstyle_dir / "strassenraumkarte.qgz") as f:
        proj = f.read("strassenraumkarte.qgs").decode("utf-8")
        proj = (proj
            .replace("@scale_factor", f"{scale_factor}")
            .replace("@project_folder", f"'{srk_mapstyle_dir}'")
            .replace("25833", crs_to.split(":")[1])
            .replace("symbols/man_made/manhole.svg", "symbols/man_made/manhole.png"))
        for layer_name in location_config.get("excludeLayers", []):
            proj = proj.replace(
                f" checked=\"Qt::Checked\" name=\"{layer_name}\"",
                f" checked=\"Qt::Unchecked\" name=\"{layer_name}\"")
        Path(srk_mapstyle_dir / "strassenraumkarte.qgs").write_text(proj)

    from processing.core import Processing
    Processing.Processing.initialize()

    print(f"{time_str()} ----- street_parking -----")
    import street_parking

    print(f"{time_str()} ----- post_processing -----")
    (srk_geojson_dir / "parking").mkdir(parents=True, exist_ok=True)
    shutil.copy(sp_data_dir / "output" / "street_parking_lines.geojson", srk_geojson_dir / "parking")

    import post_processing

if generate_tiles:
    sys.path.append(str(tw_dir))

    print(f"{time_str()} ===== Tiles =====")

    QgsProject.instance().read(str(srk_mapstyle_dir / "strassenraumkarte.qgs"))

    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "index.html").write_text(
        (this_dir / "index.html.tpl").read_text()
            .replace("${location}", location)
            .replace("${bbox[0]}", str(bbox[0]))
            .replace("${bbox[1]}", str(bbox[1]))
            .replace("${bbox[2]}", str(bbox[2]))
            .replace("${bbox[3]}", str(bbox[3])))

    import tile_writer
