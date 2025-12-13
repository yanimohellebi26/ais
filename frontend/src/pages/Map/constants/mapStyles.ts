export const MAP_STYLES = {
    GLOBE: "https://demotiles.maplibre.org/globe.json",
    STANDARD: "https://demotiles.maplibre.org/style.json"
} as const;

export const DEFAULT_VIEW_STATE = {
    longitude: -100,
    latitude: 36,
    zoom: 2.5
} as const;

export const MAP_CONFIG = {
    MIN_ZOOM: 2.5,
    MAX_ZOOM: 15
}

export const WIDGET_VIEW_STATE = {
    longitude: 0,
    latitude: 0,
    zoom: 1
} as const;

export const CLUSTER_CONFIG = {
    RADIUS: 50,
    MAX_ZOOM_NORMAL: 6,
    MAX_ZOOM_RADIUS: 2
} as const;

export const VESSEL_COLORS = {
    SELECTED: "#FF0000",
    CLICKED_POSITION: "#00FFFF",
    NORMAL: "#007BFF",
    RADIUS_CIRCLE: "#007BFF"
} as const;

export const PORT_COLORS = {
    NORMAL: "#b81b6f"
} as const;