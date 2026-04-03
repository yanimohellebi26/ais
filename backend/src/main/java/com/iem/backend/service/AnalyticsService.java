package com.iem.backend.service;

import com.iem.backend.dto.analytics.AnalyticsFilter;
import com.iem.backend.dto.analytics.CountryPresenceDetails;
import com.iem.backend.entity.CustomUserDetails;
import com.iem.backend.entity.Role;
import com.iem.backend.entity.User;
import com.iem.backend.exception.ApiExceptions;
import com.iem.backend.repository.CountryPresenceRepository;
import org.springframework.security.access.AccessDeniedException;
import org.springframework.stereotype.Service;

import java.sql.Timestamp;
import java.time.LocalDate;
import java.util.List;

@Service
public class AnalyticsService {

    private final CountryPresenceRepository countryPresenceRepository;

    public AnalyticsService(
            CountryPresenceRepository countryPresenceRepository
    ) {
        this.countryPresenceRepository = countryPresenceRepository;
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