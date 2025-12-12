package com.iem.backend.service;

import com.iem.backend.entity.Port;
import com.iem.backend.exception.ApiExceptions;
import com.iem.backend.repository.PortRepository;
import org.springframework.stereotype.Service;

import java.util.List;

@Service
public class PortService {

    private final PortRepository repository;

    public PortService(PortRepository repository) {
        this.repository = repository;
    }

    public List<Port> getPorts() {
        return repository.findAll();
    }

    public List<Port> getPortByBounds(
            double minLat, double maxLat, double minLon, double maxLon, int limit
    ) {
        validateBounds(minLat, maxLat, minLon, maxLon);

        return repository.findByBounds(minLat, maxLat, minLon, maxLon, limit);
    }

    private void validateBounds(double minLat, double maxLat, double minLon, double maxLon) {
        if (minLat < -90 || maxLat > 90 || minLat >= maxLat) {
            throw new ApiExceptions.BadRequestException("Invalid latitude");
        }
        if (minLon < -180 || maxLon > 180 || minLon >= maxLon) {
            throw new ApiExceptions.BadRequestException("Invalid longitude");
        }
    }

    public Port getNearestPort(double lon, double lat) {
        return repository.findNearestPort(lon, lat);
    }

}
