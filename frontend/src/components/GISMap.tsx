import { useEffect, useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import * as maplibregl from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";

const API_URL = "http://127.0.0.1:8000";

type Conflict = {
  id: string;
  parcel_id: string;
  conflict_type: string;
  severity: string;
  description: string;
  difference_value: number | null;
  confidence_score: number;
  recommended_action: string;
  status: string;
  created_at: string;
};

type SourceRecord = {
  owner_name: string | null;
  area: number | null;
  ward: number | null;
  latitude: number | null;
  longitude: number | null;
};

type SourceComparison = {
  success: boolean;
  parcel_id: string;
  cadastral: SourceRecord | null;
  municipal: SourceRecord | null;
};

/*
 * -------------------------------------------------------
 * PLOT TRUTH ASSESSMENT
 * -------------------------------------------------------
 */
type PlotTruthAssessment = {
  score: number;
  status: string;
  sourceAgreement: number;
  conflictCount: number;
  highSeverityCount: number;
  mediumSeverityCount: number;
  missingSource: boolean;
  likelyCause: string;
  recommendation: string;
};

type Parcel = {
  parcel_id: string;
  owner_name: string;
  area: number | null;
  score: number;
  status: string;
  conflict_count: number;
  explanation: string;
  ward: number | null;
  source_count: number;
  matching_sources: number;
};

type HarmonizationRecord = {
  parcel_id: string;
  owner_name: string;
  area: number | null;
  ward: number | null;
  harmonization_score: number;
  source_count: number;
  matching_sources: number;
  conflict_count: number;
  explanation: string;
};

type GISMapProps = {
  focusParcelId?: string | null;
  onFocusHandled?: () => void;
  compact?: boolean;
};

type Coordinate = [number, number];

type ParcelFeature = {
  type: "Feature";
  properties: Parcel;
  geometry: {
    type: "Polygon";
    coordinates: Coordinate[][];
  };
};

type ParcelGeoJSON = {
  type: "FeatureCollection";
  features: ParcelFeature[];
};

/*
 * -------------------------------------------------------
 * HAVERSINE DISTANCE
 * -------------------------------------------------------
 */
function calculateDistanceMeters(
  lat1: number | null | undefined,
  lon1: number | null | undefined,
  lat2: number | null | undefined,
  lon2: number | null | undefined
) {
  if (
    lat1 === null ||
    lat1 === undefined ||
    lon1 === null ||
    lon1 === undefined ||
    lat2 === null ||
    lat2 === undefined ||
    lon2 === null ||
    lon2 === undefined
  ) {
    return null;
  }

  const R = 6371000;

  const toRadians = (value: number) =>
    (value * Math.PI) / 180;

  const dLat = toRadians(lat2 - lat1);
  const dLon = toRadians(lon2 - lon1);

  const a =
    Math.sin(dLat / 2) ** 2 +
    Math.cos(toRadians(lat1)) *
      Math.cos(toRadians(lat2)) *
      Math.sin(dLon / 2) ** 2;

  const c =
    2 *
    Math.atan2(
      Math.sqrt(a),
      Math.sqrt(1 - a)
    );

  return R * c;
}

/*
 * -------------------------------------------------------
/*
 * -------------------------------------------------------
 * PARCEL COLOR & STATUS HELPERS
 * Priority:
 * 1. If harmonization score < 50: RED (#ef4444)
 * 2. Else if conflict_count > 0: YELLOW (#fbbf24)
 * 3. Else: GREEN (#34d399)
 * -------------------------------------------------------
 */
function getParcelColorByScoreAndConflict(score: number, conflictCount: number): string {
  if (score < 50) {
    return "#ef4444";
  }
  if (conflictCount > 0) {
    return "#fbbf24";
  }
  return "#34d399";
}

function getParcelStatus(score: number, conflictCount: number): string {
  if (score < 50) {
    return "Conflict Detected";
  }
  if (conflictCount > 0) {
    return "Review Required";
  }
  return "Harmonized";
}

function getParcelStatusColor(status: string): string {
  switch (status) {
    case "Harmonized":
      return "#34d399";

    case "Review Required":
      return "#fbbf24";

    case "Conflict Detected":
    case "Missing Source":
      return "#ef4444";

    default:
      return "#34d399";
  }
}

function getParcelColor(status: string): string {
  return getParcelStatusColor(status);
}


function getTruthScoreLabel(score: number) {
  if (score >= 80) {
    return "High Confidence";
  }

  if (score >= 60) {
    return "Review Required";
  }

  return "Conflict Detected";
}

function getTruthScoreDescription(score: number) {
  if (score >= 80) {
    return "Sources are largely consistent for this parcel.";
  }

  if (score >= 60) {
    return "Some source discrepancies require verification.";
  }

  return "Significant discrepancies were detected across sources.";
}

/*
 * -------------------------------------------------------
 * SEVERITY STYLE
 * -------------------------------------------------------
 */
function getSeverityStyle(severity: string) {
  switch (severity.toUpperCase()) {
    case "HIGH":
      return {
        badge:
          "bg-red-500/20 text-red-300 border-red-500/30",
        icon: "🔴",
      };

    case "MEDIUM":
      return {
        badge:
          "bg-yellow-500/20 text-yellow-300 border-yellow-500/30",
        icon: "🟡",
      };

    case "LOW":
      return {
        badge:
          "bg-blue-500/20 text-blue-300 border-blue-500/30",
        icon: "🔵",
      };

    default:
      return {
        badge:
          "bg-gray-500/20 text-gray-300 border-gray-500/30",
        icon: "⚪",
      };
  }
}

/*
 * -------------------------------------------------------
 * FORMAT CONFLICT TYPE
 * -------------------------------------------------------
 */
function formatConflictType(type: string) {
  return type
    .replace(/_/g, " ")
    .toLowerCase()
    .replace(/\b\w/g, (char) => char.toUpperCase());
}

/*
 * -------------------------------------------------------
 * FORMAT VALUE
 * -------------------------------------------------------
 */
function formatValue(
  value: string | number | null | undefined
) {
  if (
    value === null ||
    value === undefined ||
    value === ""
  ) {
    return "Not Available";
  }

  return String(value);
}

/*
 * -------------------------------------------------------
 * VALUES MATCH
 * -------------------------------------------------------
 */
function valuesMatch(
  first: string | number | null | undefined,
  second: string | number | null | undefined
) {
  if (
    first === null ||
    first === undefined ||
    second === null ||
    second === undefined
  ) {
    return false;
  }

  return (
    String(first).trim().toLowerCase() ===
    String(second).trim().toLowerCase()
  );
}

/*
 * -------------------------------------------------------
 * PLOT TRUTH ASSESSMENT ENGINE
 * -------------------------------------------------------
 *
 * Combines:
 *
 * Parcel
 * +
 * Conflicts
 * +
 * Cadastral / Municipal comparison
 *
 * to produce:
 *
 * Plot Truth Assessment
 */
function buildPlotTruthAssessment(
  parcel: Parcel,
  conflicts: Conflict[],
  comparison: SourceComparison | null
): PlotTruthAssessment {
  const parcelConflicts = conflicts.filter(
    (conflict) =>
      conflict.parcel_id === parcel.parcel_id
  );

  const highSeverityCount =
    parcelConflicts.filter(
      (conflict) =>
        conflict.severity.toUpperCase() === "HIGH"
    ).length;

  const mediumSeverityCount =
    parcelConflicts.filter(
      (conflict) =>
        conflict.severity.toUpperCase() === "MEDIUM"
    ).length;

  const missingSource =
    parcelConflicts.some(
      (conflict) =>
        conflict.conflict_type ===
          "MISSING_IN_MUNICIPAL" ||
        conflict.conflict_type ===
          "MISSING_IN_CADASTRAL"
    );

  let sourceAgreement = 100;

  if (comparison) {
    const totalFields = 5;
    let matchingFields = 0;

    const cadastral = comparison.cadastral;
    const municipal = comparison.municipal;

    if (cadastral && municipal) {
      if (
        valuesMatch(
          cadastral.owner_name,
          municipal.owner_name
        )
      ) {
        matchingFields++;
      }

      if (
        valuesMatch(
          cadastral.area,
          municipal.area
        )
      ) {
        matchingFields++;
      }

      if (
        valuesMatch(
          cadastral.ward,
          municipal.ward
        )
      ) {
        matchingFields++;
      }

      if (
        valuesMatch(
          cadastral.latitude,
          municipal.latitude
        )
      ) {
        matchingFields++;
      }

      if (
        valuesMatch(
          cadastral.longitude,
          municipal.longitude
        )
      ) {
        matchingFields++;
      }

      sourceAgreement =
        (matchingFields / totalFields) * 100;
    } else {
      sourceAgreement = 50;
    }
  }

  let likelyCause =
    "Records are consistent across available sources.";

  if (missingSource) {
    likelyCause =
      "A parcel record is missing from one of the source datasets.";
  } else if (
    parcelConflicts.some(
      (conflict) =>
        conflict.conflict_type ===
        "OWNER_MISMATCH"
    )
  ) {
    likelyCause =
      "Owner information appears to have been updated differently across source records.";
  } else if (
    parcelConflicts.some(
      (conflict) =>
        conflict.conflict_type ===
        "AREA_MISMATCH"
    )
  ) {
    likelyCause =
      "Land area measurements differ between source records.";
  } else if (
    parcelConflicts.some(
      (conflict) =>
        conflict.conflict_type ===
        "LOCATION_MISMATCH"
    )
  ) {
    likelyCause =
      "Survey or GIS coordinates differ between source datasets.";
  }

  let recommendation =
    "No immediate action required.";

  if (parcelConflicts.length > 0) {
    recommendation =
      parcelConflicts[0].recommended_action;
  }

  let status = "Harmonized";

  if (parcelConflicts.length > 0) {
    status =
      parcel.score >= 60
        ? "Review Required"
        : "Conflict Detected";
  }

  return {
    score: parcel.score,
    status,
    sourceAgreement,
    conflictCount: parcelConflicts.length,
    highSeverityCount,
    mediumSeverityCount,
    missingSource,
    likelyCause,
    recommendation,
  };
}

export default function GISMap({
  focusParcelId,
  onFocusHandled,
  compact = false,
}: GISMapProps) {
  const { t } = useTranslation();

  const mapContainer =
    useRef<HTMLDivElement | null>(null);

  const map =
    useRef<maplibregl.Map | null>(null);

  const parcelsRef =
    useRef<ParcelGeoJSON | null>(null);

  const parcelOverlayRef =
    useRef<HTMLDivElement | null>(null);

  const sourceMarkersRef =
    useRef<maplibregl.Marker[]>([]);

  const [selectedParcel, setSelectedParcel] =
    useState<Parcel | null>(null);

  const [mapReady, setMapReady] =
    useState(false);

  const [conflicts, setConflicts] =
    useState<Conflict[]>([]);

  const [sourceComparison, setSourceComparison] =
    useState<SourceComparison | null>(null);

  /*
   * -------------------------------------------------------
   * PHASE 8.3 — MAP STATISTICS
   * -------------------------------------------------------
   */
  const [mapStats, setMapStats] = useState({
    total: 0,
    harmonized: 0,
    review: 0,
    conflicts: 0,
  });

  /*
   * -------------------------------------------------------
   * SHOW SOURCE MARKERS
   * -------------------------------------------------------
   */
  function showSourceMarkers(
    comparison: SourceComparison | null
  ) {
    const currentMap = map.current;

    if (!currentMap) {
      return;
    }

    sourceMarkersRef.current.forEach(
      (marker) => marker.remove()
    );

    sourceMarkersRef.current = [];

    if (!comparison) {
      return;
    }

    const cadastral =
      comparison.cadastral;

    const municipal =
      comparison.municipal;

    /*
     * Cadastral marker.
     */
    if (
      cadastral?.latitude !== null &&
      cadastral?.latitude !== undefined &&
      cadastral?.longitude !== null &&
      cadastral?.longitude !== undefined
    ) {
      const element =
        document.createElement("div");

      element.style.width = "16px";
      element.style.height = "16px";
      element.style.borderRadius = "50%";
      element.style.background = "#3b82f6";
      element.style.border =
        "3px solid white";
      element.style.boxShadow =
        "0 0 12px rgba(59,130,246,0.8)";

      const marker =
        new maplibregl.Marker({
          element,
        })
          .setLngLat([
            cadastral.longitude,
            cadastral.latitude,
          ])
          .setPopup(
            new maplibregl.Popup({
              offset: 12,
            }).setHTML(
              `
                <div style="font-family: Inter, sans-serif;">
                  <strong>Cadastral Source</strong>
                  <br />
                  ${cadastral.latitude},
                  ${cadastral.longitude}
                </div>
              `
            )
          )
          .addTo(currentMap);

      sourceMarkersRef.current.push(
        marker
      );
    }

    /*
     * Municipal marker.
     */
    if (
      municipal?.latitude !== null &&
      municipal?.latitude !== undefined &&
      municipal?.longitude !== null &&
      municipal?.longitude !== undefined
    ) {
      const element =
        document.createElement("div");

      element.style.width = "16px";
      element.style.height = "16px";
      element.style.borderRadius = "50%";
      element.style.background = "#a855f7";
      element.style.border =
        "3px solid white";
      element.style.boxShadow =
        "0 0 12px rgba(168,85,247,0.8)";

      const marker =
        new maplibregl.Marker({
          element,
        })
          .setLngLat([
            municipal.longitude,
            municipal.latitude,
          ])
          .setPopup(
            new maplibregl.Popup({
              offset: 12,
            }).setHTML(
              `
                <div style="font-family: Inter, sans-serif;">
                  <strong>Municipal Source</strong>
                  <br />
                  ${municipal.latitude},
                  ${municipal.longitude}
                </div>
              `
            )
          )
          .addTo(currentMap);

      sourceMarkersRef.current.push(
        marker
      );
    }
  }

  /*
   * -------------------------------------------------------
   * SHOW SPATIAL DIFFERENCE LINE
   * -------------------------------------------------------
   */
  function showSpatialDifferenceLine(
    comparison: SourceComparison | null
  ) {
    const currentMap = map.current;

    if (!currentMap) {
      return;
    }

    if (
      currentMap.getSource(
        "source-difference"
      )
    ) {
      if (
        currentMap.getLayer(
          "source-difference-line"
        )
      ) {
        currentMap.removeLayer(
          "source-difference-line"
        );
      }

      currentMap.removeSource(
        "source-difference"
      );
    }

    if (
      !comparison?.cadastral ||
      !comparison?.municipal
    ) {
      return;
    }

    const c =
      comparison.cadastral;

    const m =
      comparison.municipal;

    if (
      c.latitude === null ||
      c.latitude === undefined ||
      c.longitude === null ||
      c.longitude === undefined ||
      m.latitude === null ||
      m.latitude === undefined ||
      m.longitude === null ||
      m.longitude === undefined
    ) {
      return;
    }

    currentMap.addSource(
      "source-difference",
      {
        type: "geojson",

        data: {
          type: "Feature",

          properties: {},

          geometry: {
            type: "LineString",

            coordinates: [
              [
                c.longitude,
                c.latitude,
              ],
              [
                m.longitude,
                m.latitude,
              ],
            ],
          },
        },
      }
    );

    currentMap.addLayer({
      id: "source-difference-line",

      type: "line",

      source: "source-difference",

      paint: {
        "line-color":
          "#f97316",

        "line-width": 3,

        "line-dasharray": [
          2,
          2,
        ],
      },
    });
  }

  /*
   * -------------------------------------------------------
   * LOAD CONFLICTS
   * -------------------------------------------------------
   */
  async function loadConflicts() {
    try {
      const response = await fetch(
        `${API_URL}/conflicts/`
      );

      if (!response.ok) {
        throw new Error(
          `Conflict API failed: ${response.status}`
        );
      }

      const data =
        (await response.json()) as {
          success: boolean;
          count: number;
          conflicts: Conflict[];
        };

      if (!data.success) {
        throw new Error(
          "Conflict API returned unsuccessful response"
        );
      }

      setConflicts(
        data.conflicts ?? []
      );

      console.log(
        `BHU-SYNC: loaded ${
          data.conflicts?.length ?? 0
        } conflicts`
      );
    } catch (error) {
      console.error(
        "BHU-SYNC: failed to load conflicts",
        error
      );

      setConflicts([]);
    }
  }

  /*
   * -------------------------------------------------------
   * LOAD SOURCE COMPARISON
   * -------------------------------------------------------
   */
  async function loadSourceComparison(
    parcelId: string
  ) {
    try {
      const response = await fetch(
        `${API_URL}/analysis/source-comparison/${encodeURIComponent(
          parcelId
        )}`
      );

      if (!response.ok) {
        throw new Error(
          `Source comparison API failed: ${response.status}`
        );
      }

      const data =
        (await response.json()) as SourceComparison;

      if (!data.success) {
        throw new Error(
          "Source comparison API returned unsuccessful response"
        );
      }

      setSourceComparison(data);

      showSourceMarkers(data);

      showSpatialDifferenceLine(data);

      console.log(
        `BHU-SYNC: loaded source comparison for ${parcelId}`
      );
    } catch (error) {
      console.error(
        "BHU-SYNC: failed to load source comparison",
        error
      );

      setSourceComparison(null);

      showSourceMarkers(null);

      showSpatialDifferenceLine(null);
    }
  }

  /*
   * -------------------------------------------------------
   * DRAW PARCELS
   * -------------------------------------------------------
   */
  const renderParcels = () => {
    const currentMap = map.current;

    const overlay =
      parcelOverlayRef.current;

    const parcelData =
      parcelsRef.current;

    if (
      !currentMap ||
      !overlay ||
      !parcelData
    ) {
      return;
    }

    overlay.innerHTML = "";

    const svgNS =
      "http://www.w3.org/2000/svg";

    const svg =
      document.createElementNS(
        svgNS,
        "svg"
      );

    svg.setAttribute(
      "width",
      "100%"
    );

    svg.setAttribute(
      "height",
      "100%"
    );

    svg.setAttribute(
      "viewBox",
      `0 0 ${currentMap.getContainer().clientWidth} ${currentMap.getContainer().clientHeight}`
    );

    svg.style.position =
      "absolute";

    svg.style.left =
      "0";

    svg.style.top =
      "0";

    svg.style.width =
      "100%";

    svg.style.height =
      "100%";

    svg.style.pointerEvents =
      "none";

    overlay.appendChild(svg);

    parcelData.features.forEach(
      (feature) => {
        if (
          !feature.geometry ||
          feature.geometry.type !==
            "Polygon"
        ) {
          return;
        }

        const coordinates =
          feature.geometry.coordinates[0];

        if (
          !coordinates ||
          coordinates.length < 3
        ) {
          return;
        }

        const points =
          coordinates.map(
            (coordinate) => {
              const point =
                currentMap.project(
                  coordinate as maplibregl.LngLatLike
                );

              return `${point.x},${point.y}`;
            }
          );

        const polygon =
          document.createElementNS(
            svgNS,
            "polygon"
          );

        polygon.setAttribute(
          "points",
          points.join(" ")
        );

        /*
         * PHASE 8.3 — STEP 9
         * Derive color from score + conflict count
         * using the new status helpers, instead of
         * only trusting the merged "status" string.
         */
        const score = Number(
          feature.properties.score ?? 0
        );

        const conflictCount = Number(
          feature.properties.conflict_count ?? 0
        );

        const color =
          getParcelColorByScoreAndConflict(
            score,
            conflictCount
          );

        /*
         * PHASE 8.3 — STEP 8
         * Highlight the parcel focused from
         * AI Copilot → View on GIS Map.
         */
        const isFocused =
          feature.properties.parcel_id ===
          focusParcelId;

        polygon.setAttribute(
          "fill",
          color
        );

        polygon.setAttribute(
          "fill-opacity",
          "0.55"
        );

        polygon.setAttribute(
          "stroke",
          isFocused ? "#ffffff" : color
        );

        polygon.setAttribute(
          "stroke-width",
          isFocused ? "4" : "2"
        );

        polygon.style.pointerEvents =
          "auto";

        polygon.style.cursor =
          "pointer";

        polygon.addEventListener(
          "click",
          (event) => {
            event.stopPropagation();

            setSelectedParcel(
              feature.properties
            );

            const clickedParcelId =
              String(
                feature.properties
                  .parcel_id ?? ""
              );

            loadSourceComparison(
              clickedParcelId
            );
          }
        );

        polygon.addEventListener(
          "mouseenter",
          () => {
            polygon.setAttribute(
              "fill-opacity",
              "0.8"
            );

            polygon.setAttribute(
              "stroke",
              "#000000"
            );

            polygon.setAttribute(
              "stroke-width",
              "4"
            );
          }
        );

        polygon.addEventListener(
          "mouseleave",
          () => {
            polygon.setAttribute(
              "fill-opacity",
              "0.55"
            );

            polygon.setAttribute(
              "stroke",
              isFocused ? "#ffffff" : color
            );

            polygon.setAttribute(
              "stroke-width",
              isFocused ? "4" : "2"
            );
          }
        );

        svg.appendChild(
          polygon
        );

        /*
         * Calculate parcel center.
         */
        let longitude = 0;
        let latitude = 0;

        coordinates.forEach(
          (coordinate) => {
            longitude +=
              coordinate[0];

            latitude +=
              coordinate[1];
          }
        );

        longitude /=
          coordinates.length;

        latitude /=
          coordinates.length;

        const center =
          currentMap.project([
            longitude,
            latitude,
          ]);

        /*
         * Parcel label.
         */
        const label =
          document.createElement(
            "div"
          );

        label.style.position =
          "absolute";

        label.style.left =
          `${center.x}px`;

        label.style.top =
          `${center.y}px`;

        label.style.transform =
          "translate(-50%, -50%)";

        label.style.background =
          "rgba(15, 23, 42, 0.90)";

        label.style.color =
          "#ffffff";

        label.style.padding =
          "4px 8px";

        label.style.borderRadius =
          "6px";

        label.style.fontSize =
          "12px";

        label.style.fontWeight =
          "700";

        label.style.whiteSpace =
          "nowrap";

        label.style.pointerEvents =
          "none";

        label.style.border =
          `2px solid ${color}`;

        label.textContent =
          feature.properties.parcel_id;

        overlay.appendChild(
          label
        );
      }
    );
  };

  useEffect(() => {
    if (
      !mapContainer.current ||
      map.current
    ) {
      return;
    }

    console.log(
      "BHU-SYNC: creating map"
    );

    const newMap =
      new maplibregl.Map({
        container:
          mapContainer.current,

        center: [
          74.4782,
          19.88495,
        ],

        zoom: 16,

        style: {
          version: 8,

          sources: {
            osm: {
              type: "raster",

              tiles: [
                "https://tile.openstreetmap.org/{z}/{x}/{y}.png",
              ],

              tileSize: 256,

              attribution:
                "© OpenStreetMap contributors",
            },
          },

          layers: [
            {
              id: "osm",

              type: "raster",

              source: "osm",
            },
          ],
        },
      });

    map.current =
      newMap;

    newMap.addControl(
      new maplibregl.NavigationControl(),
      "top-right"
    );

    newMap.on(
      "error",
      (event) => {
        console.error(
          "BHU-SYNC MapLibre Error:",
          event
        );
      }
    );

    /*
     * -------------------------------------------------------
     * MAP LOAD
     * -------------------------------------------------------
     */
    newMap.on(
      "load",
      async () => {
        console.log(
          "BHU-SYNC: map loaded"
        );

        try {
          /*
           * 1. Load GeoJSON geometry.
           */
          const response =
            await fetch(
              "/parcels.json"
            );

          if (!response.ok) {
            throw new Error(
              `Failed to load parcels.json: HTTP ${response.status}`
            );
          }

          const parcelData =
            (await response.json()) as ParcelGeoJSON;

          console.log(
            "BHU-SYNC: parcels loaded:",
            parcelData.features.length
          );

          if (
            parcelData.type !==
              "FeatureCollection" ||
            !Array.isArray(
              parcelData.features
            )
          ) {
            throw new Error(
              "Invalid GeoJSON FeatureCollection"
            );
          }

          /*
           * 2. Load harmonization data.
           */
          const backendResponse =
            await fetch(
              `${API_URL}/harmonization/`
            );

          if (!backendResponse.ok) {
            throw new Error(
              `Harmonization API failed: HTTP ${backendResponse.status}`
            );
          }

          const backendData =
            (await backendResponse.json()) as {
              success: boolean;
              count: number;
              records: HarmonizationRecord[];
            };

          if (!backendData.success) {
            throw new Error(
              "Harmonization API returned unsuccessful response"
            );
          }

          console.log(
            "BHU-SYNC: backend harmonization records:",
            backendData.records.length
          );

          console.log(
            "BHU-SYNC: Harmonization API response:",
            backendData
          );

          /*
           * PHASE 8.3 — STEP 3
           * Calculate map statistics from the
           * live harmonization records.
           */
          const statsRecords = Array.isArray(
            backendData.records
          )
            ? backendData.records
            : [];

          const total = statsRecords.length;

          const harmonizedCount = statsRecords.filter(
            (record: any) => {
              const score = Number(
                record.harmonization_score ??
                  record.score ??
                  0
              );

              const conflictCountForStats = Number(
                record.conflict_count ??
                  record.conflicts ??
                  0
              );

              return (
                conflictCountForStats === 0 &&
                score >= 80
              );
            }
          ).length;

          const conflictsCount = statsRecords.filter(
            (record: any) => {
              return (
                Number(
                  record.conflict_count ??
                    record.conflicts ??
                    0
                ) > 0
              );
            }
          ).length;

          const reviewCount = statsRecords.filter(
            (record: any) => {
              const score = Number(
                record.harmonization_score ??
                  record.score ??
                  0
              );

              const conflictCountForStats = Number(
                record.conflict_count ??
                  record.conflicts ??
                  0
              );

              return !(
                conflictCountForStats === 0 &&
                score >= 80
              );
            }
          ).length;

          setMapStats({
            total,
            harmonized: harmonizedCount,
            review: reviewCount,
            conflicts: conflictsCount,
          });

          /*
           * 3. Load conflicts.
           */
          await loadConflicts();

          /*
           * 4. Backend lookup.
           */
          const harmonizationLookup =
            new Map<
              string,
              HarmonizationRecord
            >();

          backendData.records.forEach(
            (record) => {
              harmonizationLookup.set(
                record.parcel_id,
                record
              );
            }
          );

          /*
           * 5. Merge backend data.
           */
          const mergedParcelData: ParcelGeoJSON =
            {
              ...parcelData,

              features:
                parcelData.features.map(
                  (feature) => {
                    const parcelId =
                      feature.properties
                        .parcel_id;

                    const backendRecord =
                      harmonizationLookup.get(
                        parcelId
                      );

                    if (
                      !backendRecord
                    ) {
                      return feature;
                    }

                    const score = Number(
                      backendRecord.harmonization_score ?? 0
                    );
                    const conflictCount = Number(
                      backendRecord.conflict_count ?? 0
                    );
                    const status = getParcelStatus(
                      score,
                      conflictCount
                    );


                    return {
                      ...feature,

                      properties: {
                        ...feature.properties,

                        parcel_id:
                          backendRecord.parcel_id,

                        owner_name:
                          backendRecord.owner_name,

                        area:
                          backendRecord.area,

                        score:
                          backendRecord.harmonization_score,

                        status,

                        conflict_count:
                          backendRecord.conflict_count,

                        explanation:
                          backendRecord.explanation,

                        ward:
                          backendRecord.ward,

                        source_count:
                          backendRecord.source_count,

                        matching_sources:
                          backendRecord.matching_sources,
                      },
                    };
                  }
                ),
            };

          console.log(
            "BHU-SYNC: merged GIS data:",
            mergedParcelData
          );

          /*
           * 6. Store merged data.
           */
          parcelsRef.current =
            mergedParcelData;

          setMapReady(true);

          /*
           * 7. Add GeoJSON source.
           */
          if (
            !newMap.getSource(
              "parcels"
            )
          ) {
            newMap.addSource(
              "parcels",
              {
                type: "geojson",

                data:
                  mergedParcelData as any,
              }
            );
          }

          /*
           * 8. Add fill.
           */
          if (
            !newMap.getLayer(
              "parcel-fill"
            )
          ) {
            newMap.addLayer({
              id: "parcel-fill",

              type: "fill",

              source: "parcels",

              paint: {
                "fill-color": [
                  "match",
                  ["get", "status"],

                  "Harmonized",
                  "#34d399",

                  "Review Required",
                  "#fbbf24",

                  "Conflict Detected",
                  "#ef4444",

                  "Missing Source",
                  "#ef4444",

                  "#34d399",
                ],

                "fill-opacity":
                  0.18,
              },
            });
          }

          /*
           * 9. Add outline.
           */
          if (
            !newMap.getLayer(
              "parcel-outline"
            )
          ) {
            newMap.addLayer({
              id: "parcel-outline",

              type: "line",

              source: "parcels",

              paint: {
                "line-color":
                  "#ffffff",

                "line-width":
                  2,

                "line-opacity":
                  0.9,
              },
            });
          }

          /*
           * 10. Calculate bounds.
           */
          const bounds =
            new maplibregl.LngLatBounds();

          mergedParcelData.features.forEach(
            (feature) => {
              feature.geometry.coordinates.forEach(
                (ring) => {
                  ring.forEach(
                    (coordinate) => {
                      bounds.extend(
                        coordinate
                      );
                    }
                  );
                }
              );
            }
          );

          if (!bounds.isEmpty()) {
            console.log(
              "BHU-SYNC: fitting map to parcels"
            );

            newMap.fitBounds(
              bounds,
              {
                padding: 100,

                maxZoom: 18,

                duration: 0,
              }
            );
          }

          /*
           * 11. Create parcel overlay.
           */
          if (
            !parcelOverlayRef.current
          ) {
            const overlay =
              document.createElement(
                "div"
              );

            overlay.style.position =
              "absolute";

            overlay.style.left =
              "0";

            overlay.style.top =
              "0";

            overlay.style.width =
              "100%";

            overlay.style.height =
              "100%";

            overlay.style.pointerEvents =
              "none";

            overlay.style.zIndex =
              "5";

            newMap
              .getContainer()
              .appendChild(
                overlay
              );

            parcelOverlayRef.current =
              overlay;
          }

          /*
           * 12. First render.
           */
          setTimeout(() => {
            renderParcels();
          }, 100);

          /*
           * 13. Keep overlay attached.
           */
          newMap.on(
            "move",
            renderParcels
          );

          newMap.on(
            "zoom",
            renderParcels
          );

          newMap.on(
            "resize",
            renderParcels
          );

          newMap.on(
            "moveend",
            renderParcels
          );

          newMap.on(
            "zoomend",
            renderParcels
          );

          /*
           * 14. MAP CLICK.
           */
          newMap.on(
            "click",
            (event) => {
              const point =
                event.point;

              const features =
                newMap.queryRenderedFeatures(
                  [
                    [
                      point.x - 2,
                      point.y - 2,
                    ],
                    [
                      point.x + 2,
                      point.y + 2,
                    ],
                  ],
                  {
                    layers: [
                      "parcel-fill",
                    ],
                  }
                );

              if (
                features.length ===
                0
              ) {
                return;
              }

              const properties =
                features[0]
                  .properties;

              if (!properties) {
                return;
              }

              const parcel: Parcel =
                {
                  parcel_id:
                    String(
                      properties.parcel_id ??
                        ""
                    ),

                  owner_name:
                    String(
                      properties.owner_name ??
                        ""
                    ),

                  area:
                    properties.area ===
                      null ||
                    properties.area ===
                      undefined ||
                    properties.area ===
                      ""
                      ? null
                      : Number(
                          properties.area
                        ),

                  score:
                    Number(
                      properties.score ??
                        0
                    ),

                  status:
                    String(
                      properties.status ??
                        "Unknown"
                    ),

                  conflict_count:
                    Number(
                      properties.conflict_count ??
                        0
                    ),

                  explanation:
                    String(
                      properties.explanation ??
                        ""
                    ),

                  ward:
                    properties.ward ===
                      null ||
                    properties.ward ===
                      undefined ||
                    properties.ward ===
                      ""
                      ? null
                      : Number(
                          properties.ward
                        ),

                  source_count:
                    Number(
                      properties.source_count ??
                        0
                    ),

                  matching_sources:
                    Number(
                      properties.matching_sources ??
                        0
                    ),
                };

              console.log(
                "BHU-SYNC: selected parcel:",
                parcel
              );

              setSelectedParcel(
                parcel
              );

              const clickedParcelId =
                String(
                  properties.parcel_id ??
                    ""
                );

              loadSourceComparison(
                clickedParcelId
              );
            }
          );

          console.log(
            "BHU-SYNC: parcel map ready"
          );
        } catch (error) {
          console.error(
            "BHU-SYNC: parcel setup failed:",
            error
          );
        }
      }
    );

    /*
     * -------------------------------------------------------
     * CLEANUP
     * -------------------------------------------------------
     */
    return () => {
      console.log(
        "BHU-SYNC: removing MapLibre map"
      );

      sourceMarkersRef.current.forEach(
        (marker) => marker.remove()
      );

      sourceMarkersRef.current =
        [];

      if (
        map.current?.getSource(
          "source-difference"
        )
      ) {
        if (
          map.current.getLayer(
            "source-difference-line"
          )
        ) {
          map.current.removeLayer(
            "source-difference-line"
          );
        }

        map.current.removeSource(
          "source-difference"
        );
      }

      if (
        parcelOverlayRef.current
      ) {
        parcelOverlayRef.current.remove();

        parcelOverlayRef.current =
          null;
      }

      newMap.remove();

      map.current =
        null;

      parcelsRef.current =
        null;

      setMapReady(false);
    };
  }, []);

  useEffect(() => {
    if (
      !focusParcelId ||
      !mapReady ||
      !map.current ||
      !parcelsRef.current
    ) {
      return;
    }

    const feature =
      parcelsRef.current.features.find(
        (parcelFeature) =>
          parcelFeature.properties.parcel_id ===
          focusParcelId
      );

    if (!feature) {
      onFocusHandled?.();
      return;
    }

    const currentMap = map.current;
    const bounds = new maplibregl.LngLatBounds();

    feature.geometry.coordinates.forEach(
      (ring) => {
        ring.forEach((coordinate) => {
          bounds.extend(coordinate);
        });
      }
    );

    setSelectedParcel(feature.properties);
    void loadSourceComparison(focusParcelId);

    if (!bounds.isEmpty()) {
      currentMap.fitBounds(bounds, {
        padding: 120,
        maxZoom: 18,
        duration: 700,
      });
    }

    renderParcels();

    onFocusHandled?.();
  }, [
    focusParcelId,
    mapReady,
    onFocusHandled,
  ]);

  /*
   * -------------------------------------------------------
   * SELECTED PARCEL CONFLICTS
   * -------------------------------------------------------
   */
  const selectedParcelConflicts =
    selectedParcel
      ? conflicts.filter(
          (conflict) =>
            conflict.parcel_id ===
            selectedParcel.parcel_id
        )
      : [];

  /*
   * -------------------------------------------------------
   * PLOT TRUTH ASSESSMENT
   * -------------------------------------------------------
   */
  const plotTruth =
    selectedParcel
      ? buildPlotTruthAssessment(
          selectedParcel,
          conflicts,
          sourceComparison
        )
      : null;

  /*
   * -------------------------------------------------------
   * SPATIAL DIFFERENCE
   * -------------------------------------------------------
   */
  const spatialDifference =
    sourceComparison?.cadastral &&
    sourceComparison?.municipal
      ? calculateDistanceMeters(
          sourceComparison.cadastral.latitude,
          sourceComparison.cadastral.longitude,
          sourceComparison.municipal.latitude,
          sourceComparison.municipal.longitude
        )
      : null;

  const truthScore = plotTruth?.score ?? 0;
  const truthConflictCount =
    plotTruth?.conflictCount ?? selectedParcel?.conflict_count ?? 0;
  const truthStatus = getTruthScoreLabel(truthScore);
  const truthDescription =
    getTruthScoreDescription(truthScore);
  const sourceCount = selectedParcel?.source_count ?? 0;
  const missingSource = sourceCount > 0 && sourceCount < 2;

  return (
    <div className={compact ? "h-full" : "space-y-6"}>

      {/* =====================================
          PHASE 8.3 — GIS HEADER
      ===================================== */}
      {!compact && (
        <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
        <div>
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl border border-blue-500/20 bg-blue-500/10">
              🗺️
            </div>

            <div>
              <h1 className="text-2xl font-semibold text-white">
                {t("gis.title")}
              </h1>

              <p className="mt-1 text-sm text-slate-400">
                {t("gis.subtitle")}
              </p>
            </div>
          </div>
        </div>

        <div className="rounded-xl border border-slate-800 bg-slate-900/70 px-4 py-3">
          <div className="flex items-center gap-2 text-xs text-slate-400">
            <span className="h-2 w-2 rounded-full bg-emerald-400" />
            {t("common.live")} GIS Intelligence
          </div>
        </div>
        </div>
      )}

      {/* =====================================
          PHASE 8.3 — STATISTICS CARDS
      ===================================== */}
      {!compact && (
        <div className="grid grid-cols-2 gap-4 xl:grid-cols-4">
        <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-4">
          <p className="text-xs font-medium uppercase tracking-wider text-slate-500">
            {t("common.total")} {t("dataHub.datasets")}
          </p>

          <p className="mt-2 text-2xl font-semibold text-white">
            {mapStats.total}
          </p>

          <p className="mt-1 text-xs text-slate-400">
            {t("gis.map")}
          </p>
        </div>

        <div className="rounded-2xl border border-emerald-500/20 bg-slate-900/70 p-4">
          <p className="text-xs font-medium uppercase tracking-wider text-slate-500">
            Harmonized
          </p>

          <p className="mt-2 text-2xl font-semibold text-emerald-400">
            {mapStats.harmonized}
          </p>

          <p className="mt-1 text-xs text-slate-400">
            {t("plotTruth.highConfidence")}
          </p>
        </div>

        <div className="rounded-2xl border border-amber-500/20 bg-slate-900/70 p-4">
          <p className="text-xs font-medium uppercase tracking-wider text-slate-500">
            Review Required
          </p>

          <p className="mt-2 text-2xl font-semibold text-amber-400">
            {mapStats.review}
          </p>

          <p className="mt-1 text-xs text-slate-400">
            {t("plotTruth.verificationRequired")}
          </p>
        </div>

        <div className="rounded-2xl border border-red-500/20 bg-slate-900/70 p-4">
          <p className="text-xs font-medium uppercase tracking-wider text-slate-500">
            {t("conflicts.conflicts")}
          </p>

          <p className="mt-2 text-2xl font-semibold text-red-400">
            {mapStats.conflicts}
          </p>

          <p className="mt-1 text-xs text-slate-400">
            {t("sourceComparison.mismatch")}
          </p>
        </div>
        </div>
      )}

      {/* =====================================
          MAP + LEGEND + SELECTED PARCEL PANEL
          (unchanged, kept relative for legend/panel overlay)
      ===================================== */}
      <div
        className={`relative w-full overflow-hidden rounded-xl ${
          compact ? "h-full" : "h-[700px]"
        }`}
      >

        {/* MAP */}
        <div
          ref={mapContainer}
          className="absolute inset-0 w-full h-full"
        />

        {/* LEGEND */}
        {!compact && (
          <div className="absolute bottom-5 left-5 z-20 bg-slate-950/95 border border-slate-800 rounded-xl p-5 shadow-xl">

          <h3 className="text-white font-semibold mb-4">
            {t("gis.parcels")}
          </h3>

          <div className="space-y-3 text-sm text-slate-200">

            <div className="flex items-center gap-3">
              <span className="w-3 h-3 rounded-sm bg-green-500" />

              <span>
                {t("gis.harmonized")}
              </span>
            </div>

            <div className="flex items-center gap-3">
              <span className="w-3 h-3 rounded-sm bg-yellow-500" />

              <span>
                {t("gis.reviewRequired")}
              </span>
            </div>

            <div className="flex items-center gap-3">
              <span className="w-3 h-3 rounded-sm bg-red-500" />

              <span>
                {t("gis.conflict")}
              </span>
            </div>

          </div>

          {/* SOURCE LOCATION LEGEND */}
          <div className="mt-2 rounded-lg border border-white/10 bg-black/70 p-3 backdrop-blur">

            <p className="mb-2 text-[10px] font-semibold uppercase tracking-wide text-gray-400">
              {t("sourceComparison.source")}
            </p>

            <div className="space-y-1.5 text-[11px]">

              <div className="flex items-center gap-2">

                <span className="h-3 w-3 rounded-full border-2 border-white bg-blue-500" />

                <span className="text-gray-300">
                  Cadastral
                </span>

              </div>

              <div className="flex items-center gap-2">

                <span className="h-3 w-3 rounded-full border-2 border-white bg-purple-500" />

                <span className="text-gray-300">
                  Municipal
                </span>

              </div>

            </div>

          </div>

          </div>
        )}

        {/* -------------------------------------------------
            SELECTED PARCEL / PLOT TRUTH PANEL
           ------------------------------------------------- */}
        {!compact && selectedParcel && (
          <div className="absolute top-5 right-5 z-30 w-80 max-h-[650px] overflow-y-auto bg-slate-950/95 border border-slate-800 rounded-xl p-5 shadow-xl">

            {/* PLOT TRUTH HEADER */}
            <div className="border-b border-slate-800 px-1 pb-4">

              <div className="flex items-start justify-between gap-4">

                <div>

                  <div className="flex items-center gap-2">
                    <span className="text-lg">🔎</span>

                    <h2 className="text-sm font-semibold text-white">
                      {t("plotTruth.title")}
                    </h2>
                  </div>

                  <p className="mt-1 text-xs text-slate-400">
                    Explainable parcel harmonization assessment
                  </p>
                  <p className="mt-1 text-[11px] text-gray-500">
                    {selectedParcel.parcel_id}
                  </p>

                </div>

                <span className="rounded-lg border border-blue-500/20 bg-blue-500/10 px-2.5 py-1 text-[10px] font-medium uppercase tracking-wider text-blue-300">
                  AI Analysis
                </span>
              </div>

            </div>

            <div className="space-y-4 mt-5">

              {/* -------------------------------------------------
                  TRUTH SCORE
                 ------------------------------------------------- */}
              <div className="rounded-xl border border-white/10 bg-white/[0.03] p-4">

                <div className="flex items-start justify-between gap-3">

                  <div>

                    <p className="text-[10px] font-semibold uppercase tracking-wide text-gray-500">
                      Harmonization Score
                    </p>

                    <p className="mt-1 text-3xl font-bold text-white">
                      {truthScore.toFixed(0)}
                      <span className="ml-1 text-lg text-slate-500">
                        /100
                      </span>
                    </p>

                  </div>

                  <div className="text-right">

                    <span
                      className={`inline-flex rounded-lg px-3 py-1.5 text-xs font-semibold ${
                        truthScore >= 80
                          ? "bg-emerald-500/10 text-emerald-400"
                          : truthScore >= 60
                          ? "bg-amber-500/10 text-amber-400"
                          : "bg-red-500/10 text-red-400"
                      }`}
                    >
                      {truthStatus}
                    </span>

                  </div>

                </div>

                <p className="mt-4 text-sm leading-6 text-slate-400">
                  {truthDescription}
                </p>

                <div className="mt-3 h-2 overflow-hidden rounded-full bg-white/10">

                  <div
                    className={`h-full rounded-full ${
                      (plotTruth?.score ?? 0) >=
                      80
                        ? "bg-green-500"
                        : (plotTruth?.score ?? 0) >=
                          60
                        ? "bg-yellow-500"
                        : "bg-red-500"
                    }`}
                    style={{
                      width: `${Math.max(
                        0,
                        Math.min(
                          100,
                          plotTruth?.score ?? 0
                        )
                      )}%`,
                    }}
                  />

                </div>

              </div>

              <div className="mt-5">
                <div className="mb-2 flex items-center justify-between">
                  <span className="text-sm font-medium text-slate-300">
                    Source Agreement
                  </span>
                  <span className="text-xs font-semibold text-slate-400">
                    {truthScore}%
                  </span>
                </div>

                <div className="h-2 overflow-hidden rounded-full bg-slate-800">
                  <div
                    className={`h-full rounded-full ${
                      truthScore >= 80
                        ? "bg-emerald-400"
                        : truthScore >= 60
                        ? "bg-amber-400"
                        : "bg-red-400"
                    }`}
                    style={{
                      width: `${Math.max(
                        0,
                        Math.min(100, truthScore)
                      )}%`,
                    }}
                  />
                </div>

                <p className="mt-2 text-xs leading-5 text-slate-500">
                  Agreement indicator derived from available source attributes and harmonization checks.
                </p>
              </div>

              <div className="mt-5 rounded-xl border border-slate-800 bg-slate-900/50 p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-xs uppercase tracking-wider text-slate-500">
                      {t("conflicts.totalConflicts")}
                    </p>
                    <p className="mt-1 text-sm font-medium text-white">
                      {truthConflictCount === 0
                        ? t("conflicts.noConflicts")
                        : `${truthConflictCount} conflict${
                            truthConflictCount === 1 ? "" : "s"
                          } detected`}
                    </p>
                  </div>
                  <span className="text-2xl">
                    {truthConflictCount === 0 ? "✓" : "⚠"}
                  </span>
                </div>
              </div>

              <div className="mt-5">
                <div className="mb-3 flex items-center gap-2">
                  <span>🧠</span>
                  <h3 className="text-sm font-semibold text-white">
                    {t("plotTruth.overallAssessment")}
                  </h3>
                </div>

                {truthConflictCount === 0 ? (
                  <div className="rounded-xl border border-emerald-500/20 bg-emerald-500/5 p-4">
                    <p className="text-sm text-emerald-300">
                      {t("conflicts.noConflicts")}
                    </p>
                    <p className="mt-1 text-xs leading-5 text-slate-400">
                      Available parcel attributes are consistent across the harmonized sources.
                    </p>
                  </div>
                ) : (
                  <div className="rounded-xl border border-amber-500/20 bg-amber-500/5 p-4">
                    <p className="text-sm font-medium text-amber-300">
                      {t("plotTruth.whyFlagged")}
                    </p>
                    <p className="mt-2 text-xs leading-5 text-slate-400">
                      BHU-SYNC detected discrepancies between available cadastral, municipal, registry, or spatial records. The parcel requires verification by the responsible authority.
                    </p>
                  </div>
                )}
              </div>

              {missingSource && (
                <div className="mt-4 rounded-xl border border-red-500/20 bg-red-500/5 p-4">
                  <div className="flex items-start gap-3">
                    <span className="text-lg">⚠️</span>
                    <div>
                      <p className="text-sm font-medium text-red-300">
                        Missing Source Data
                      </p>
                      <p className="mt-1 text-xs leading-5 text-slate-400">
                        This parcel is not available in all expected harmonization sources. Additional verification is recommended.
                      </p>
                    </div>
                  </div>
                </div>
              )}

              <div className="mt-5 rounded-xl border border-blue-500/20 bg-blue-500/5 p-4">
                <p className="text-xs font-semibold uppercase tracking-wider text-blue-400">
                    {t("plotTruth.recommendedAction")}
                </p>
                <p className="mt-2 text-sm leading-6 text-slate-300">
                  {truthConflictCount === 0 && truthScore >= 80
                    ? "No immediate investigation is indicated based on the available source data."
                    : truthConflictCount > 0
                    ? "Review the conflicting source records and verify the parcel with the responsible department."
                    : "Review the available source records before finalizing the parcel assessment."}
                </p>
              </div>

              <div className="mt-5 border-t border-slate-800 pt-4">
                <p className="text-[11px] leading-5 text-slate-500">
                  BHU-SYNC provides analytical and explainable harmonization insights. This assessment does not constitute a legal determination of ownership, title, or boundary rights. Final decisions remain with the authorized department.
                </p>
              </div>

              {/* -------------------------------------------------
                  SOURCE HEALTH
                 ------------------------------------------------- */}
              <div className="grid grid-cols-2 gap-2">

                <div className="rounded-lg border border-blue-500/20 bg-blue-500/5 p-3">

                  <p className="text-[10px] uppercase tracking-wide text-blue-300">
                    Cadastral
                  </p>

                  <p className="mt-1 text-sm font-semibold text-white">
                    {sourceComparison?.cadastral
                      ? "Available"
                      : "Missing"}
                  </p>

                </div>

                <div className="rounded-lg border border-purple-500/20 bg-purple-500/5 p-3">

                  <p className="text-[10px] uppercase tracking-wide text-purple-300">
                    Municipal
                  </p>

                  <p className="mt-1 text-sm font-semibold text-white">
                    {sourceComparison?.municipal
                      ? "Available"
                      : "Missing"}
                  </p>

                </div>

              </div>

              {/* -------------------------------------------------
                  BASIC PARCEL INFORMATION
                 ------------------------------------------------- */}

              {/* PARCEL ID */}
              <div>
                <p className="text-xs text-slate-500 mb-1">
                  Parcel ID
                </p>

                <p className="text-white font-medium">
                  {
                    selectedParcel.parcel_id
                  }
                </p>
              </div>

              {/* OWNER */}
              <div>
                <p className="text-xs text-slate-500 mb-1">
                  Owner
                </p>

                <p className="text-white">
                  {
                    selectedParcel.owner_name
                  }
                </p>
              </div>

              {/* AREA */}
              <div>
                <p className="text-xs text-slate-500 mb-1">
                  Area
                </p>

                <p className="text-white">
                  {selectedParcel.area ===
                  null
                    ? "Not Available"
                    : `${selectedParcel.area} sq. m`}
                </p>
              </div>

              {/* WARD */}
              <div>
                <p className="text-xs text-slate-500 mb-1">
                  Ward
                </p>

                <p className="text-white">
                  {selectedParcel.ward ===
                  null
                    ? "Not Available"
                    : selectedParcel.ward}
                </p>
              </div>

              {/* SOURCE MATCHING */}
              <div>
                <p className="text-xs text-slate-500 mb-1">
                  Source Matching
                </p>

                <p className="text-white">
                  {
                    selectedParcel.matching_sources
                  }{" "}
                  /{" "}
                  {
                    selectedParcel.source_count
                  }{" "}
                  sources
                </p>
              </div>

              {/* -------------------------------------------------
                  STATUS
                 ------------------------------------------------- */}
              <div>

                <p className="text-xs text-slate-500 mb-2">
                  Status
                </p>

                <span
                  className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium"
                  style={{
                    backgroundColor:
                      `${getParcelColor(
                        selectedParcel.status
                      )}22`,

                    color:
                      getParcelColor(
                        selectedParcel.status
                      ),

                    border:
                      `1px solid ${getParcelColor(
                        selectedParcel.status
                      )}55`,
                  }}
                >
                  {
                    selectedParcel.status
                  }
                </span>

              </div>

              {/* -------------------------------------------------
                  CONFLICT SUMMARY
                 ------------------------------------------------- */}
              <div>

                <div className="mt-4 grid grid-cols-3 gap-2">

                  <div className="rounded-lg bg-white/5 p-3">

                    <p className="text-[10px] text-gray-500">
                      TOTAL
                    </p>

                    <p className="mt-1 text-lg font-bold text-white">
                      {
                        plotTruth?.conflictCount
                      }
                    </p>

                  </div>

                  <div className="rounded-lg bg-red-500/10 p-3">

                    <p className="text-[10px] text-red-300">
                      HIGH
                    </p>

                    <p className="mt-1 text-lg font-bold text-red-300">
                      {
                        plotTruth?.highSeverityCount
                      }
                    </p>

                  </div>

                  <div className="rounded-lg bg-yellow-500/10 p-3">

                    <p className="text-[10px] text-yellow-300">
                      MEDIUM
                    </p>

                    <p className="mt-1 text-lg font-bold text-yellow-300">
                      {
                        plotTruth?.mediumSeverityCount
                      }
                    </p>

                  </div>

                </div>

              </div>

              {/* -------------------------------------------------
                  WHY IS THIS PLOT FLAGGED?
                 ------------------------------------------------- */}
              <div className="rounded-xl border border-orange-500/20 bg-orange-500/5 p-4">

                <div className="flex items-center gap-2">

                  <span className="text-base">
                    🔎
                  </span>

                  <h3 className="text-sm font-bold text-orange-300">
                    WHY IS THIS PLOT FLAGGED?
                  </h3>

                </div>

                {plotTruth &&
                plotTruth.conflictCount >
                  0 ? (
                  <>

                    <p className="mt-3 text-xs leading-5 text-gray-300">

                      BHU-SYNC detected{" "}

                      <span className="font-semibold text-white">
                        {
                          plotTruth.conflictCount
                        }
                      </span>{" "}

                      data consistency issue
                      {plotTruth.conflictCount ===
                      1
                        ? ""
                        : "s"}{" "}
                      across the available source
                      records.

                    </p>

                    <div className="mt-3 space-y-2">

                      {selectedParcelConflicts.map(
                        (conflict) => {

                          const severityStyle =
                            getSeverityStyle(
                              conflict.severity
                            );

                          return (
                            <div
                              key={
                                conflict.id
                              }
                              className="flex gap-2 rounded-lg bg-black/20 p-2.5"
                            >

                              <span>
                                {
                                  severityStyle.icon
                                }
                              </span>

                              <div>

                                <p className="text-xs font-semibold text-white">
                                  {
                                    formatConflictType(
                                      conflict.conflict_type
                                    )
                                  }
                                </p>

                                <p className="mt-0.5 text-[11px] leading-4 text-gray-400">
                                  {
                                    conflict.description
                                  }
                                </p>

                              </div>

                            </div>
                          );
                        }
                      )}

                    </div>

                  </>
                ) : (
                  <p className="mt-3 text-xs leading-5 text-green-300">
                    ✓ No significant discrepancies were
                    detected across the available source
                    records.
                  </p>
                )}

              </div>

              {/* -------------------------------------------------
                  LIKELY CAUSE
                 ------------------------------------------------- */}
              <div>

                <p className="text-[10px] font-semibold uppercase tracking-wide text-gray-500">
                  Likely Cause
                </p>

                <p className="mt-1 text-xs leading-5 text-gray-300">
                  {plotTruth?.likelyCause}
                </p>

              </div>

              {/* -------------------------------------------------
                  RECOMMENDED ACTION
                 ------------------------------------------------- */}
              <div className="rounded-lg border border-white/10 bg-white/[0.03] p-3">

                <p className="text-[10px] font-semibold uppercase tracking-wide text-gray-500">
                  Recommended Action
                </p>

                <p className="mt-1 text-xs leading-5 text-gray-300">
                  {plotTruth?.recommendation}
                </p>

              </div>

              {/* -------------------------------------------------
                  OLD EXPLANATION
                 ------------------------------------------------- */}
              <div className="border-t border-slate-800 pt-4">

                <p className="text-xs text-slate-500 mb-2">
                  DATA EXPLANATION
                </p>

                <div className="bg-slate-900 rounded-lg p-3">

                  <p className="text-sm text-slate-300 leading-relaxed">
                    {
                      selectedParcel.explanation ||
                      "No discrepancy explanation available."
                    }
                  </p>

                </div>

              </div>

              {/* -------------------------------------------------
                  CONFLICT DETAILS
                 ------------------------------------------------- */}
              <div className="mt-5 border-t border-white/10 pt-4">

                <div className="flex items-center justify-between mb-3">

                  <h3 className="text-sm font-semibold text-white">
                    CONFLICT DETAILS
                  </h3>

                  <span className="text-xs text-gray-400">
                    {
                      selectedParcelConflicts.length
                    }{" "}
                    conflict
                    {selectedParcelConflicts.length ===
                    1
                      ? ""
                      : "s"}
                  </span>

                </div>

                {selectedParcelConflicts.length ===
                0 ? (
                  <div className="rounded-lg border border-green-500/20 bg-green-500/10 p-3">

                    <p className="text-sm text-green-300">
                      ✓ No conflicts detected for this
                      parcel.
                    </p>

                  </div>
                ) : (
                  <div className="space-y-3">

                    {selectedParcelConflicts.map(
                      (conflict) => {

                        const severityStyle =
                          getSeverityStyle(
                            conflict.severity
                          );

                        return (
                          <div
                            key={
                              conflict.id
                            }
                            className="rounded-lg border border-white/10 bg-black/20 p-3"
                          >

                            <div className="flex items-center justify-between gap-2">

                              <span
                                className={`rounded-md border px-2 py-1 text-[10px] font-semibold ${severityStyle.badge}`}
                              >
                                {
                                  severityStyle.icon
                                }{" "}
                                {
                                  conflict.severity
                                }
                              </span>

                              <span className="text-[10px] text-gray-500">
                                {
                                  conflict.status
                                }
                              </span>

                            </div>

                            <p className="mt-2 text-sm font-semibold text-white">
                              {
                                formatConflictType(
                                  conflict.conflict_type
                                )
                              }
                            </p>

                            <p className="mt-1 text-xs leading-5 text-gray-400">
                              {
                                conflict.description
                              }
                            </p>

                            {conflict.difference_value !==
                              null && (
                              <div className="mt-2 rounded-md bg-white/5 px-2 py-1.5">

                                <p className="text-[11px] text-gray-400">
                                  Difference
                                </p>

                                <p className="text-sm font-medium text-white">
                                  {
                                    conflict.difference_value
                                  }{" "}
                                  m²
                                </p>

                              </div>
                            )}

                            <div className="mt-3">

                              <p className="text-[10px] font-semibold uppercase tracking-wide text-gray-500">
                                Recommended Action
                              </p>

                              <p className="mt-1 text-xs leading-5 text-gray-300">
                                {
                                  conflict.recommended_action
                                }
                              </p>

                            </div>

                          </div>
                        );
                      }
                    )}

                  </div>
                )}

              </div>

              {/* -------------------------------------------------
                  SOURCE COMPARISON
                 ------------------------------------------------- */}
              <div className="mt-5 border-t border-white/10 pt-4">

                <div className="mb-3">

                  <h3 className="text-sm font-semibold text-white">
                    {t("sourceComparison.title")}
                  </h3>

                  <p className="mt-1 text-[11px] text-gray-500">
                    {t("sourceComparison.subtitle")}
                  </p>

                </div>

                {sourceComparison ? (
                  <div>

                    <div className="overflow-hidden rounded-2xl border border-slate-800 bg-slate-900/70">

                      {/* TABLE HEADER */}
                      <div className="grid grid-cols-3 border-b border-slate-800 bg-slate-950/40">

                        <div className="px-5 py-3 text-left text-xs font-medium uppercase tracking-wider text-slate-400">
                          Field
                        </div>

                        <div className="border-l border-slate-800 px-5 py-3 text-left text-xs font-medium uppercase tracking-wider text-slate-400">
                          Cadastral
                        </div>

                        <div className="border-l border-slate-800 px-5 py-3 text-left text-xs font-medium uppercase tracking-wider text-slate-400">

                          Municipal

                          {!sourceComparison.municipal && (
                            <span className="ml-1 text-red-400">
                              Missing
                            </span>
                          )}

                        </div>

                      </div>

                      {/* COMPARISON ROWS */}
                      {[
                        {
                          label: "Owner",

                          cadastral:
                            sourceComparison
                              .cadastral
                              ?.owner_name,

                          municipal:
                            sourceComparison
                              .municipal
                              ?.owner_name,
                        },

                        {
                          label: "Area",

                          cadastral:
                            sourceComparison
                              .cadastral
                              ?.area !== null &&
                            sourceComparison
                              .cadastral
                              ?.area !==
                              undefined
                              ? `${sourceComparison.cadastral.area} m²`
                              : null,

                          municipal:
                            sourceComparison
                              .municipal
                              ?.area !== null &&
                            sourceComparison
                              .municipal
                              ?.area !==
                              undefined
                              ? `${sourceComparison.municipal.area} m²`
                              : null,
                        },

                        {
                          label: "Ward",

                          cadastral:
                            sourceComparison
                              .cadastral
                              ?.ward,

                          municipal:
                            sourceComparison
                              .municipal
                              ?.ward,
                        },

                        {
                          label: "Latitude",

                          cadastral:
                            sourceComparison
                              .cadastral
                              ?.latitude,

                          municipal:
                            sourceComparison
                              .municipal
                              ?.latitude,
                        },

                        {
                          label: "Longitude",

                          cadastral:
                            sourceComparison
                              .cadastral
                              ?.longitude,

                          municipal:
                            sourceComparison
                              .municipal
                              ?.longitude,
                        },
                      ].map((row) => {

                        const same =
                          valuesMatch(
                            row.cadastral,
                            row.municipal
                          );

                        return (
                          <div
                            key={
                              row.label
                            }
                            className="grid grid-cols-3 border-b border-slate-800/70 transition-colors hover:bg-slate-800/30"
                          >

                            <div className="px-5 py-4 text-sm font-medium text-white">
                              {
                                row.label
                              }
                            </div>

                            <div
                              className={`border-l border-slate-800 px-5 py-4 text-sm ${
                                row.cadastral === null ||
                                row.cadastral === undefined
                                  ? "text-red-300"
                                  : same
                                  ? "text-emerald-300"
                                  : "bg-amber-500/10 text-amber-300"
                              }`}
                            >
                              {
                                formatValue(
                                  row.cadastral
                                )
                              }
                            </div>

                            <div
                              className={`border-l border-slate-800 px-5 py-4 text-sm ${
                                row.municipal === null ||
                                row.municipal === undefined
                                  ? "text-red-300"
                                  : same
                                  ? "text-emerald-300"
                                  : "bg-amber-500/10 text-amber-300"
                              }`}
                            >
                              {
                                formatValue(
                                  row.municipal
                                )
                              }
                            </div>

                          </div>
                        );
                      })}

                    </div>

                    {/* SPATIAL DIFFERENCE */}
                    {spatialDifference !==
                      null && (
                      <div className="mt-3 rounded-lg border border-orange-500/20 bg-orange-500/10 p-3">

                        <div className="flex items-center justify-between">

                          <div>

                            <p className="text-[10px] font-semibold uppercase tracking-wide text-orange-300">
                              Spatial Difference
                            </p>

                            <p className="mt-1 text-lg font-bold text-white">
                              {
                                spatialDifference.toFixed(
                                  2
                                )
                              }{" "}
                              m
                            </p>

                          </div>

                          <div className="text-2xl">
                            📍
                          </div>

                        </div>

                        <p className="mt-1 text-[11px] leading-5 text-orange-200/70">
                          Distance between the cadastral
                          and municipal coordinates.
                        </p>

                      </div>
                    )}

                    {/* COMPARISON LEGEND */}
                    <div className="mt-2 flex items-center gap-4 text-[10px] text-gray-500">

                      <div className="flex items-center gap-1">

                        <span className="h-2 w-2 rounded-sm bg-red-500/60" />

                        <span>
                          Difference detected
                        </span>

                      </div>

                      <div className="flex items-center gap-1">

                        <span className="h-2 w-2 rounded-sm bg-white/20" />

                        <span>
                          Matching
                        </span>

                      </div>

                    </div>

                    {/* SOURCE CONFLICT SUMMARY */}
                    {selectedParcelConflicts.length >
                      0 && (
                      <div className="mt-3 rounded-lg border border-yellow-500/20 bg-yellow-500/10 p-3">

                        <div className="flex items-center gap-2">

                          <span className="text-sm">
                            ⚠
                          </span>

                          <p className="text-xs font-semibold text-yellow-300">
                            Source discrepancy detected
                          </p>

                        </div>

                        <p className="mt-1 text-[11px] leading-5 text-yellow-200/70">
                          BHU-SYNC detected{" "}
                          {
                            selectedParcelConflicts.length
                          }{" "}
                          conflicting record
                          {selectedParcelConflicts.length ===
                          1
                            ? ""
                            : "s"}{" "}
                          across the available sources.
                        </p>

                      </div>
                    )}

                  </div>
                ) : (
                  <div className="rounded-lg border border-white/10 bg-white/5 p-3">

                    <p className="text-xs text-gray-400">
                      Loading source comparison...
                    </p>

                  </div>
                )}

              </div>

            </div>
          </div>
        )}

      </div>

    </div>
  );
}