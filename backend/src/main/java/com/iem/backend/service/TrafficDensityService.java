package com.iem.backend.service;

import com.iem.backend.dto.analytics.TrafficDensity;
import com.iem.backend.repository.projection.TrafficDensityProjection;
import com.iem.backend.entity.CustomUserDetails;
import com.iem.backend.entity.Role;
import com.iem.backend.entity.User;
import com.iem.backend.exception.ApiExceptions;
import com.iem.backend.repository.TrafficDensityRepository;
import org.springframework.security.access.AccessDeniedException;
import com.iem.backend.exception.ApiExceptions.*;
import org.springframework.stereotype.Service;

import java.util.List;
import java.sql.Timestamp;
import java.time.LocalDate;
import java.util.*;
import java.util.stream.Collectors;

@Service
public class TrafficDensityService {

    private final TrafficDensityRepository trafficDensityRepository;

    public TrafficDensityService(TrafficDensityRepository trafficDensityRepository) {
        this.trafficDensityRepository = trafficDensityRepository;
    }

    public List<TrafficDensity> getTrafficDensity(
            CustomUserDetails currentUser, double minLat, double maxLat, double minLon, double maxLon,
            Optional<LocalDate> dateStartOpt, Optional<LocalDate> dateEndOpt, double gridSize
    ){
        User user = currentUser.getUser();
        Role userRole = user.getRole();

        checkAccess(userRole);

        validateBounds(minLat, maxLat, minLon, maxLon);

        if (gridSize <= 0) {
            throw new BadRequestException("gridSize must be greater than 0");
        }

        List<TrafficDensityProjection> results;

        if(dateStartOpt.isEmpty() && dateEndOpt.isEmpty()){
            //No Date, latest positions
            results = trafficDensityRepository.findTrafficDensityLatest(minLat, maxLat, minLon, maxLon, gridSize);
        } else {
            LocalDate dateStart =  dateStartOpt.orElse(LocalDate.now());
            LocalDate dateEnd =  dateEndOpt.orElse(dateStart);

            if (dateEnd.isBefore(dateStart)) {
                throw new BadRequestException("End date must be after or equal to start date");
            }

            Timestamp start = Timestamp.valueOf(dateStart.atStartOfDay());
            Timestamp end = Timestamp.valueOf(dateEnd.atTime(23, 59, 59));

            results = trafficDensityRepository.findTrafficDensityByDate(minLat, maxLat, minLon, maxLon, start, end, gridSize);
        }

        if (results.isEmpty()) {
            return Collections.emptyList();
        }

        return results.stream()
                .map(p -> new TrafficDensity(
                        p.getLat(),
                        p.getLon(),
                        p.getDensity()
                ))
                .collect(Collectors.toList());
    }

    private void validateBounds(double minLat, double maxLat, double minLon, double maxLon) {
        if (minLat < -90 || maxLat > 90 || minLat >= maxLat) {
            throw new ApiExceptions.BadRequestException("Invalid latitude");
        }
        if (minLon < -180 || maxLon > 180 || minLon >= maxLon) {
            throw new ApiExceptions.BadRequestException("Invalid longitude");
        }
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