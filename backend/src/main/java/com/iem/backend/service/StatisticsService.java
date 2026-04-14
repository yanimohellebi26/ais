package com.iem.backend.service;

import com.iem.backend.dto.analytics.AnalyticsFilter;
import com.iem.backend.dto.statistics.VesselTypeStats;
import com.iem.backend.entity.CustomUserDetails;
import com.iem.backend.entity.Role;
import com.iem.backend.entity.User;
import com.iem.backend.exception.ApiExceptions;
import com.iem.backend.repository.VesselTypeStatsRepository;
import com.iem.backend.repository.projection.VesselTypeStatsProjection;
import org.springframework.security.access.AccessDeniedException;
import org.springframework.stereotype.Service;

import java.util.List;
import java.sql.Timestamp;
import java.time.LocalDate;

@Service
public class StatisticsService {

    private final VesselTypeStatsRepository vesselTypeStatsRepository;

    public StatisticsService(VesselTypeStatsRepository vesselTypeStatsRepository) {
        this.vesselTypeStatsRepository = vesselTypeStatsRepository;
    }

    public List<VesselTypeStats> getAllVesselTypeStats(
            CustomUserDetails currentUser, AnalyticsFilter filters, int topN
    ) {
        User user = currentUser.getUser();
        Role userRole = user.getRole();

        checkAccess(userRole);
        validateGeoFilter(filters);

        Timestamp startTimestamp = null;
        Timestamp endTimestamp = null;

        LocalDate startDate = filters.startDate();
        LocalDate endDate = filters.endDate();

        if (startDate != null ||  endDate != null) {
            LocalDate dateStart = startDate != null ? startDate : LocalDate.now();
            LocalDate dateEnd = endDate != null ? endDate : dateStart;

            if (dateEnd.isBefore(dateStart)) {
                throw new ApiExceptions.BadRequestException("End date must be after or equal to start date");
            }

            startTimestamp = Timestamp.valueOf(dateStart.atStartOfDay());
            endTimestamp = Timestamp.valueOf(dateEnd.atTime(23, 59, 59));
        }

        boolean hasDate = startTimestamp != null && endTimestamp != null;
        boolean hasGeo = filters.latitude() != null;

        List<VesselTypeStatsProjection> results;

        if (hasDate) {
            if (hasGeo) {
                results = vesselTypeStatsRepository.getVesselTypeStatsByDateInRadius(
                        startTimestamp, endTimestamp,
                        filters.latitude(), filters.longitude(), filters.radius(),
                        filters.vesselType(), filters.vesselGroup(), filters.country(), topN
                );
            } else {
                results = vesselTypeStatsRepository.getVesselTypeStatsByDate(
                        startTimestamp, endTimestamp,
                        filters.vesselType(), filters.vesselGroup(), filters.country(), topN
                );
            }
        } else {
            if (hasGeo) {
                results = vesselTypeStatsRepository.getVesselTypeStatsInRadius(
                        filters.latitude(), filters.longitude(), filters.radius(),
                        filters.vesselType(), filters.vesselGroup(), filters.country(), topN
                );
            } else {
                results = vesselTypeStatsRepository.getVesselTypeStatsAll(
                        filters.vesselType(), filters.vesselGroup(), filters.country(), topN
                );
            }
        }

        return results.stream()
                .map(p -> new VesselTypeStats(
                        p.getVesselTypeId(),
                        p.getVesselTypeDescription(),
                        p.getVesselGroup(),
                        p.getTrajectoryCount(),
                        p.getTotalDistanceKm(),
                        p.getAvgSpeedKmh(),
                        p.getAvgDistanceKm(),
                        p.getTotalDurationHours(),
                        p.getAvgDurationHours(),
                        p.getEfficiencyKmh()
                ))
                .toList();
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

    private void validateGeoFilter(AnalyticsFilter filters) {
        boolean hasGeo = filters.latitude() != null && filters.longitude() != null && filters.radius() != null;
        boolean hasPartialGeo = filters.latitude() != null || filters.longitude() != null || filters.radius() != null;

        if (hasPartialGeo && !hasGeo) {
            throw new ApiExceptions.BadRequestException("Latitude, longitude and radius must all be provided together");
        }
    }
}
