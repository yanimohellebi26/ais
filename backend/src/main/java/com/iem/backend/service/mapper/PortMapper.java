package com.iem.backend.service.mapper;

import com.iem.backend.dto.ports.PortGeoJson;
import com.iem.backend.entity.Port;
import org.springframework.stereotype.Component;

import java.util.List;
import java.util.Map;

@Component
public class PortMapper {

    public PortGeoJson toGeoJson(Port p) {
        Map<String, Object> props = Map.of(
                "portId", p.getId(),
                "name", p.getName(),
                "code", p.getCode()
        );
        Map<String, Object> geom = Map.of(
                "type", "Point",
                "coordinates", new double[]{p.getGeom().getX(), p.getGeom().getY()}
        );
        return new PortGeoJson("Feature", props, geom);
    }

    public List<PortGeoJson> toGeoJson(List<Port> ports) {
        return ports.stream().map(this::toGeoJson).toList();
    }

}
