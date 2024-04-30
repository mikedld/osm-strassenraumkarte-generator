<!DOCTYPE html>
<html>
<head>
  <title>${location} - Straßenraumkarte Neukölln</title>
  <meta charset="utf-8" />

  <meta name="viewport" content="width=device-width, initial-scale=1.0">

  <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
  <style type="text/css">
    html, body, #map {
      padding: 0;
      margin: 0;
      width: 100%;
      height: 100%;
      background-color: #ededed;
    }
  </style>
  <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
  <script src="https://unpkg.com/leaflet-hash@0.2.1/leaflet-hash.js"></script>
</head>
<body>
  <div id="map"></div>
  <script>
    const optionsFromHash = L.Hash.parseHash(window.location.hash);
    const bbox = [[${bbox[0]}, ${bbox[1]}], [${bbox[2]}, ${bbox[3]}]]

    const options = {
      center: optionsFromHash.center || [(bbox[0][0] + bbox[1][0]) / 2, (bbox[0][1] + bbox[1][1]) / 2],
      zoom: optionsFromHash.zoom || 15,
      minZoom: 15,
      zoomControl: true,
      maxBounds: bbox,
    };

    const map = L.map('map', options);
    const hash = new L.Hash(map);

    const mytile = L.tileLayer('./tiles/{z}/{x}/{y}.jpg', {
      maxZoom: 21,
      tms: false,
      attribution: 'Map data &copy; <a href="https://openstreetmap.org/copyright">OpenStreetMap</a> contributors | Map style &copy <a href="https://github.com/SupaplexOSM/strassenraumkarte-neukoelln">Straßenraumkarte Neukölln</a>'
    }).addTo(map);
  </script>
</body>
</html>
