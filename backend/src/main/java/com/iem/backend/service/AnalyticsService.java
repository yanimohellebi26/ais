package com.iem.backend.service;

import com.iem.backend.dto.analytics.AnalyticsFilter;
import com.iem.backend.dto.analytics.CountryPresenceDetails;
import com.iem.backend.dto.analytics.TrafficDensity;
import com.iem.backend.entity.CustomUserDetails;
import com.iem.backend.entity.Role;
import com.iem.backend.entity.User;
import com.iem.backend.exception.ApiExceptions;
import com.iem.backend.repository.CountryPresenceRepository;
import com.iem.backend.repository.TrafficDensityRepository;
import com.iem.backend.repository.projection.TrafficDensityProjection;
import org.springframework.security.access.AccessDeniedException;
import org.springframework.stereotype.Service;

import java.sql.Timestamp;
import java.time.LocalDate;
import java.util.Collections;
import java.util.List;
import java.util.stream.Collectors;

@Service
public class AnalyticsService {

    private final CountryPresenceRepository countryPresenceRepository;
    private final TrafficDensityRepository trafficDensityRepository;

    public AnalyticsService(
            CountryPresenceRepository countryPresenceRepository,
            TrafficDensityRepository trafficDensityRepository
    ) {
        this.countryPresenceRepository = countryPresenceRepository;
        this.trafficDensityRepository = trafficDensityRepository;
    }

    public List<CountryPresenceDetails> getCountryPresence(CustomUserDetails currentUser, AnalyticsFilter filter, int topN) {

        User user = currentUser.getUser();
        Role userRole = user.getRole();

        checkAccess(userRole);

        LocalDate startDate = filter.startDate();
        LocalDate endDate   = filter.endDate();
        boolean hasDate     = startDate != null || endDate != null;
        boolean hasGeo      = filter.latitude()  != null
                && filter.longitude() != null
                && filter.radius()    != null;

        if (hasDate) {
            LocalDate dateStart = startDate != null ? startDate : LocalDate.now();
            LocalDate dateEnd   = endDate   != null ? endDate   : dateStart;

            if (dateEnd.isBefore(dateStart)) {
                throw new ApiExceptions.BadRequestException("End date must be after or equal to start date");
            }

            Timestamp start = Timestamp.valueOf(dateStart.atStartOfDay());
            Timestamp end   = Timestamp.valueOf(dateEnd.atTime(23, 59, 59));

            List<Object[]> rows = hasGeo
                    ? countryPresenceRepository.findTopCountriesInRadiusByDate(
                        filter.latitude(), filter.longitude(), filter.radius(),
                        start, end,
                        filter.vesselType(), filter.vesselGroup(), filter.country(), topN)
                        : countryPresenceRepository.findTopCountriesByDate(
                        start, end,
                        filter.vesselType(), filter.vesselGroup(), filter.country(), topN);

            return toResult(rows);

        } else {
            List<Object[]> rows = hasGeo
                    ? countryPresenceRepository.findTopCountriesInRadius(filter.latitude(), filter.longitude(), filter.radius(),
                    filter.vesselType(), filter.vesselGroup(), filter.country(), topN)
                    : countryPresenceRepository.findTopCountries(filter.vesselType(), filter.vesselGroup(), filter.country(), topN);

            return toResult(rows);
        }
    }

    private List<CountryPresenceDetails> toResult(List<Object[]> rows) {
        return rows.stream()
                .map(r -> new CountryPresenceDetails(
                        (String) r[0],
                        (String) r[1],
                        ((Number) r[2]).longValue()
                ))
                .toList();
    }

    public List<TrafficDensity> getTrafficDensity(
            CustomUserDetails currentUser, double minLat, double maxLat, double minLon, double maxLon,
            double gridSize, AnalyticsFilter filters
    ){
        User user = currentUser.getUser();
        Role userRole = user.getRole();

        checkAccess(userRole);

        validateBounds(minLat, maxLat, minLon, maxLon);

        if (gridSize <= 0) {
            throw new ApiExceptions.BadRequestException("gridSize must be greater than 0");
        }

        List<TrafficDensityProjection> results;

        LocalDate startDate = filters.startDate();
        LocalDate endDate = filters.endDate();

        if(startDate == null && endDate == null){
            //No Date, latest positions
            results = trafficDensityRepository.findTrafficDensityLatest(
                    minLat, maxLat, minLon, maxLon,
                    gridSize,
                    filters.vesselType(),
                    filters.vesselGroup(),
                    filters.country()
            );
        } else {
            LocalDate dateStart = startDate != null ? startDate : LocalDate.now();
            LocalDate dateEnd = endDate != null ? endDate : dateStart;

            if (dateEnd.isBefore(dateStart)) {
                throw new ApiExceptions.BadRequestException("End date must be after or equal to start date");
            }

            Timestamp start = Timestamp.valueOf(dateStart.atStartOfDay());
            Timestamp end = Timestamp.valueOf(dateEnd.atTime(23, 59, 59));

            results = trafficDensityRepository.findTrafficDensityByDate(
                    minLat, maxLat, minLon, maxLon,
                    start, end,
                    gridSize,
                    filters.vesselType(),
                    filters.vesselGroup(),
                    filters.country()
            );
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

    private void checkAccess(Role role) {
        boolean isFullAccess = switch (role.getName()) {
            case "ADMIN", "MARITIME_EXPERT", "FINANCIAL_ANALYST" -> true;
            default -> false;
        };
        if(!isFullAccess) {
            throw new AccessDeniedException("Unauthorized Role");
        }
    }

    private void validateBounds(double minLat, double maxLat, double minLon, double maxLon) {
        if (minLat < -90 || maxLat > 90 || minLat >= maxLat) {
            throw new ApiExceptions.BadRequestException("Invalid latitude");
        }
        if (minLon < -180 || maxLon > 180 || minLon >= maxLon) {
            throw new ApiExceptions.BadRequestException("Invalid longitude");
        }
    }
}