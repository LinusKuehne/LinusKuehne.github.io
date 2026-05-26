/* Hiking page: per-hike mini maps + overview map of all hike start points.
 *
 * Reads the JSON island #hikes-data, fetches each hike's GPX, parses only
 * <trkpt lat lon> elements (waypoints intentionally ignored), then draws:
 *   - one polyline per hike inside its .hike-map div
 *   - one circle-marker per hike on #hikes-overview-map, popup linking to the entry
 *
 * Routes are fetched once per hike and reused for both the mini map and the
 * overview marker location (first trkpt).
 */

(function () {
  "use strict";

  // Swisstopo topographic basemap + official hiking-trail overlay (no API key
  // needed, see https://api3.geo.admin.ch/services/sdiservices.html).
  const BASE_TILE_URL =
    "https://wmts.geo.admin.ch/1.0.0/ch.swisstopo.pixelkarte-farbe/default/current/3857/{z}/{x}/{y}.jpeg";
  const HIKING_OVERLAY_URL =
    "https://wmts.geo.admin.ch/1.0.0/ch.swisstopo.swisstlm3d-wanderwege/default/current/3857/{z}/{x}/{y}.png";
  const TILE_ATTR =
    '&copy; <a href="https://www.swisstopo.admin.ch/" target="_blank" rel="noopener">swisstopo</a>';
  const TILE_MAX_ZOOM = 18;
  const POLYLINE_COLOR = "#1f6feb";
  const POLYLINE_WEIGHT = 5;
  const POLYLINE_CASING_COLOR = "#ffffff";
  const POLYLINE_CASING_WEIGHT = 9;
  const MARKER_FILL = "#e91e63";
  const MARKER_STROKE = "#ffffff";
  const MARKER_RADIUS = 10;
  const MARKER_STROKE_WEIGHT = 3;
  const MINI_MAP_PADDING = [10, 10];

  function parseGpxTrack(gpxText) {
    const xml = new DOMParser().parseFromString(gpxText, "application/xml");
    const points = [];
    const trkpts = xml.getElementsByTagName("trkpt");
    for (let i = 0; i < trkpts.length; i++) {
      const lat = parseFloat(trkpts[i].getAttribute("lat"));
      const lon = parseFloat(trkpts[i].getAttribute("lon"));
      if (!isNaN(lat) && !isNaN(lon)) {
        points.push([lat, lon]);
      }
    }
    return points;
  }

  function addTileLayers(map) {
    L.tileLayer(BASE_TILE_URL, {
      maxZoom: TILE_MAX_ZOOM,
      attribution: TILE_ATTR,
    }).addTo(map);
    L.tileLayer(HIKING_OVERLAY_URL, {
      maxZoom: TILE_MAX_ZOOM,
      opacity: 0.9,
    }).addTo(map);
  }

  function renderMiniMap(container, track) {
    const map = L.map(container, {
      scrollWheelZoom: false,
      attributionControl: true,
    });
    addTileLayers(map);
    // White "casing" stroke under the colored polyline so the route stays
    // legible over the busy Swisstopo basemap.
    L.polyline(track, {
      color: POLYLINE_CASING_COLOR,
      weight: POLYLINE_CASING_WEIGHT,
      opacity: 0.85,
      lineCap: "round",
      lineJoin: "round",
    }).addTo(map);
    const line = L.polyline(track, {
      color: POLYLINE_COLOR,
      weight: POLYLINE_WEIGHT,
      opacity: 1,
      lineCap: "round",
      lineJoin: "round",
    }).addTo(map);
    map.fitBounds(line.getBounds(), { padding: MINI_MAP_PADDING });
    return map;
  }

  function renderOverviewMap(container, hikes) {
    const map = L.map(container);
    addTileLayers(map);

    const markers = [];
    hikes.forEach((h) => {
      if (!h.start) return;
      const marker = L.circleMarker(h.start, {
        radius: MARKER_RADIUS,
        color: MARKER_STROKE,
        weight: MARKER_STROKE_WEIGHT,
        fillColor: MARKER_FILL,
        fillOpacity: 1,
        className: "hike-overview-marker",
      }).addTo(map);
      const safeName = document.createElement("div");
      safeName.textContent = h.name;
      marker.bindPopup(
        '<a href="#hike-' + h.slug + '">' + safeName.innerHTML + "</a>",
      );
      marker.on("click", () => {
        const entry = document.getElementById("hike-" + h.slug);
        if (entry) {
          history.replaceState(null, "", "#hike-" + h.slug);
          entry.scrollIntoView({ behavior: "smooth", block: "start" });
        }
      });
      markers.push(marker);
    });

    if (markers.length === 0) {
      // No hikes yet — show a sensible default view of Switzerland.
      map.setView([46.8, 8.2], 7);
    } else if (markers.length === 1) {
      map.setView(markers[0].getLatLng(), 11);
    } else {
      const group = L.featureGroup(markers);
      map.fitBounds(group.getBounds(), { padding: [30, 30] });
    }
  }

  function loadHike(hike) {
    return fetch(hike.gpx)
      .then((r) => {
        if (!r.ok) throw new Error("Failed to fetch " + hike.gpx);
        return r.text();
      })
      .then((text) => {
        const track = parseGpxTrack(text);
        const container = document.querySelector(
          '.hike-entry[data-slug="' + hike.slug + '"] .hike-map',
        );
        if (container && track.length > 0) {
          renderMiniMap(container, track);
        }
        return { ...hike, start: track.length > 0 ? track[0] : null };
      })
      .catch((err) => {
        console.error("Hike load failed:", hike.slug, err);
        return { ...hike, start: null };
      });
  }

  function init() {
    if (typeof L === "undefined") {
      console.warn("Leaflet not loaded; hiking maps disabled.");
      return;
    }
    const dataEl = document.getElementById("hikes-data");
    const overviewEl = document.getElementById("hikes-overview-map");
    if (!dataEl || !overviewEl) return;

    let hikes;
    try {
      hikes = JSON.parse(dataEl.textContent);
    } catch (e) {
      console.error("Failed to parse hikes data:", e);
      return;
    }

    Promise.all(hikes.map(loadHike)).then((withStarts) => {
      renderOverviewMap(overviewEl, withStarts);
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
