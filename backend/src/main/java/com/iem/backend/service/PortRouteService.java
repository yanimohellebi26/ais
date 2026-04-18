package com.iem.backend.service;

import java.util.List;

import org.springframework.security.access.AccessDeniedException;
import org.springframework.stereotype.Service;

import com.iem.backend.dto.analytics.AnalyticsFilter;
import com.iem.backend.entity.CustomUserDetails;
import com.iem.backend.entity.Role;
import com.iem.backend.repository.PortRouteRepository;
import com.iem.backend.repository.projection.PortRouteProjection;

@Service
public class PortRouteService {
    
    private final PortRouteRepository repository;

    public PortRouteService(PortRouteRepository repository) {
        this.repository = repository;
    }

    public String getRoutesAsFeatureCollection(CustomUserDetails currentUser, AnalyticsFilter filters) {
        checkAccess(currentUser.getUser().getRole());
        
        List<PortRouteProjection> results = repository.getRoutesGeoJson(
                filters.startDate(),
                filters.endDate(),
                filters.latitude(),
                filters.longitude(),
                filters.radius()
        );

        StringBuilder sb = new StringBuilder();
        sb.append("{\"type\": \"FeatureCollection\", \"features\": [");
        
        for (int i = 0; i < results.size(); i++) {
            PortRouteProjection p = results.get(i);
            sb.append(String.format(
                "{\"type\": \"Feature\", \"geometry\": %s, \"properties\": {" +
                "\"srcPort\": \"%s\", \"destPort\": \"%s\", \"count\": %d, \"avgDuration\": %.2f" +
                "}}",
                p.getGeojson(), p.getSrcPortName(), p.getDestPortName(), p.getShipCount(), p.getAvgDuration()
            ));
            if (i < results.size() - 1) sb.append(",");
        }
        
        sb.append("]}");
        return sb.toString();
    }

    private void checkAccess(Role role) {
        boolean isFullAccess = switch (role.getName()) {
            case "ADMIN", "MARITIME_EXPERT", "FINANCIAL_ANALYST" -> true;
            default -> false;
        };
        if(!isFullAccess) {
            throw new AccessDeniedException("Unauthorized Role");
        }
    }
}
