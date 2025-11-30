export const createRadiusCircle = (
    lng: number,
    lat: number,
    radiusKm: number,
    points: number = 64
) => {
    const coords: number[][] = [];

    for (let i = 0; i <= points; i++) {
        const angle = (i * 360) / points;
        const dx = radiusKm * Math.cos((angle * Math.PI) / 180);
        const dy = radiusKm * Math.sin((angle * Math.PI) / 180);

        const newLng = lng + (dx / 111.32) / Math.cos((lat * Math.PI) / 180);
        const newLat = lat + dy / 110.574;

        coords.push([newLng, newLat]);
    }

    return {
        type: "FeatureCollection" as const,
        features: [{
            type: "Feature" as const,
            geometry: {
                type: "Polygon" as const,
                coordinates: [coords]
            },
            properties: {}
        }]
    };
};