# Straßenraumkarte Generator

This project contains a script to automate map data rendering based on Straßenraumkarte Neukölln, simplifying things a bit and making it all suitable for locations other than Neukölln.

## Usage

Prerequisites:

* [QGIS](https://qgis.org/) — I've tested with 3.28 and later on 3.36; with Python support enabled
* [osmtogeojson](https://github.com/tyrasd/osmtogeojson)
* [curl](https://curl.se/)

Then:

* Clone this repository, with submodules, e.g. `git clone --recurse-submodules https://github.com/mikedld/osm-strassenraumkarte-generator`
* Adjust config.json and index.html.tpl files to your liking
* Run the script, e.g. `./generate.py Lisboa`, or simply `./generate.py` (without arguments) to list available locations

Generated map tiles and index.html will be placed under output/ subdirectory.

## Configuration

config.json file contains a map of locations to their configuration, e.g. in its simplest form

```json
{
  "locations": {
    "foo": {
      "bbox": [1, 2, 3, 4]
    }
  }
}
```

Where

* `foo` — location name, passed to the script via command line and injected into generated index.html file (if referenced in the template)
  * `bbox` — array of 4 floating-point numbers, two pairs of coordinates in EPSG:4326 (a.k.a. WGS 84), i.e. `[lat1, lon1, lat2, lon2]`
  * `settings` — optional map of overrides in case a particular step fails and is hard to fix

Inside of generate.py script file there's a number of `generate_*` variables that control whether a particular stage needs to be executed or not.
There are setting variables in street_parking.py, post_processing.py, and tile_writer.py files as well, with some of them configurable in generate.py file via environment variables.

## Copyright

This project is made available under GNU GPL version 3.
Other projects included as submodules have their own licenses.
