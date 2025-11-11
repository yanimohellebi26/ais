package com.iem.backend.service.mapper;

import com.iem.backend.dto.positionVessel.PositionVesselGeoJson;
import com.iem.backend.dto.positionVessel.VesselPositionRadiusDTO;
import com.iem.backend.entity.PositionVessel;
import org.springframework.stereotype.Component;

import java.util.List;
import java.util.Map;

@Component
public class PositionVesselMapper {

    public PositionVesselGeoJson toGeoJson(PositionVessel p) {
        Map<String, Object> props = Map.of(
                "vesselId", p.getVesselId(),
                "status", p.getStatus() != null ? p.getStatus().getId() : 0
        );
        Map<String, Object> geom = Map.of(
                "type", "Point",
                "coordinates", new double[]{p.getGeom().getX(), p.getGeom().getY()}
        );
        return new PositionVesselGeoJson("Feature", props, geom);
    }

    public List<PositionVesselGeoJson> toGeoJson(List<PositionVessel> positions) {
        return positions.stream().map(this::toGeoJson).toList();
    }

    public PositionVesselGeoJson toGeoJson(VesselPositionRadiusDTO dto) {
        Map<String, Object> props = Map.of(
                "mmsi", dto.mmsi(),
                "distance_km", dto.distanceKm(),
                "timestamp", dto.timestamp()
        );
        Map<String, Object> geom = Map.of(
                "type", "Point",
                "coordinates", new double[]{dto.longitude(), dto.latitude()}
        );
        return new PositionVesselGeoJson("Feature", props, geom);
    }

    public List<PositionVesselGeoJson> toGeoJsonFromDTOs(List<VesselPositionRadiusDTO> positions) {
        return positions.stream()
                .map(this::toGeoJson)
                .toList();
    }


}

