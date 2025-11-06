package com.iem.backend.service;

import com.iem.backend.entity.CustomUserDetails;
import com.iem.backend.entity.PositionVessel;
import com.iem.backend.entity.Role;
import com.iem.backend.entity.User;
import com.iem.backend.exception.ApiExceptions.*;
import com.iem.backend.repository.PositionVesselRepository;

import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.security.access.AccessDeniedException;
import org.springframework.stereotype.Service;

import java.sql.Timestamp;
import java.time.LocalDate;
import java.util.List;
import java.util.Optional;

@Service
public class PositionVesselService {

    private final PositionVesselRepository repository;

    private final VesselService vesselService;

    public PositionVesselService(PositionVesselRepository repository,VesselService vesselService) {
        this.repository = repository;
        this.vesselService = vesselService;
    }

    public List<PositionVessel> getPositionsByDateAndBounds(
            LocalDate dateStart, Optional<LocalDate> dateEnd,
            double minLat, double maxLat, double minLon, double maxLon
    ) {

        validateBounds(minLat, maxLat, minLon, maxLon);

        LocalDate finalDateEnd = dateEnd.orElse(dateStart);
        if (finalDateEnd.isBefore(dateStart)) {
            throw new BadRequestException("End date must be after start date");
        }

        Timestamp start = Timestamp.valueOf(dateStart.atStartOfDay());
        Timestamp end = Timestamp.valueOf(finalDateEnd.atTime(23, 59, 59));

        return repository.findByDateAndBounds(start, end, minLat, maxLat, minLon, maxLon);
    }

    public List<PositionVessel> getPositionsByIdAndOptionalDate(
            Integer vesselId, Optional<LocalDate> dateStartOpt, Optional<LocalDate> dateEndOpt, User currentUser
    ) {

        List<String> allowed = List.of("ADMIN","MARITIME_EXPERT","FINANCIAL_ANALYST");
        if (!allowed.contains(currentUser.getRole().getName())) {
            vesselService.checkUserHasAccessToVessel(currentUser,vesselId);
        }

        List<PositionVessel> positionVessels;

        if (dateStartOpt.isEmpty() && dateEndOpt.isEmpty()) {
            // No date, all positions
            positionVessels = repository.findPositionVesselsByVesselId(vesselId);
        } else {

            LocalDate startDate = dateStartOpt.orElse(LocalDate.now());
            LocalDate endDate = dateEndOpt.orElse(startDate);

            if (endDate.isBefore(startDate)) {
                throw new BadRequestException("End date must be after or equal to start date");
            }

            Timestamp start = Timestamp.valueOf(startDate.atStartOfDay());
            Timestamp end = Timestamp.valueOf(endDate.atTime(23, 59, 59));

            positionVessels = repository.findPositionVesselsByVesselIdAndBaseDateTimeBetween(vesselId, start, end);
        }

        if (positionVessels.isEmpty()) {
            throw new NotFoundException(
                    "Positions not found: either the vessel does not exist, or it has no positions for the given date range"
            );
        }

        return positionVessels;
    }


    private void validateBounds(double minLat, double maxLat, double minLon, double maxLon) {
        if (minLat < -90 || maxLat > 90 || minLat >= maxLat) {
            throw new BadRequestException("Invalid latitude");
        }
        if (minLon < -180 || maxLon > 180 || minLon >= maxLon) {
            throw new BadRequestException("Invalid longitude");
        }
    }

    public List<PositionVessel> getLatestPositions(CustomUserDetails customUserDetails, List<String> mmsisFilter, Pageable pageable) {

        User user = customUserDetails.getUser();      
        Role userRole = user.getRole();

        boolean isFullAccess = switch (userRole.getName()) {
            case "ADMIN", "MARITIME_EXPERT", "FINANCIAL_ANALYST" -> true;
            case "OWNER", "CAPTAIN" -> false;
            default -> throw new AccessDeniedException("Unauthorized Role");
        };

        if (!isFullAccess) {
            vesselService.checkUserHasAccessToVessels(user, mmsisFilter);
        }

        Page<PositionVessel> positions;

        if (mmsisFilter != null && !mmsisFilter.isEmpty()) {
            List<Integer> vesselIds = vesselService.getVesselIdsByMmsis(mmsisFilter);
            positions = repository.findLatestPositionVesselsByIdIn(vesselIds, pageable);
        } else {

            if (!isFullAccess) {
                List<Integer> userVesselIds = vesselService.getVesselIdsByUser(user.getId());

                if (userVesselIds == null || userVesselIds.isEmpty()) {
                    positions = Page.empty(pageable);
                } else {
                    positions = repository.findLatestPositionVesselsByIdIn(userVesselIds, pageable);
                }
                
            } else {
                positions = repository.findAll(pageable);
            }
        }

        return positions.getContent();
    }

    public List<PositionVessel> getLatestPositionsInBounds(
        CustomUserDetails customUserDetails,
        double minLat, double maxLat, double minLon, double maxLon,
        int limit
    ) {
        User user = customUserDetails.getUser();
        Role userRole = user.getRole();

        boolean isFullAccess = switch (userRole.getName()) {
            case "ADMIN", "MARITIME_EXPERT", "FINANCIAL_ANALYST" -> true;
            case "OWNER", "CAPTAIN" -> false;
            default -> throw new AccessDeniedException("Unauthorized Role");
        };

        if (!isFullAccess) {
            vesselService.checkUserHasAccessToVessels(user, null);
        }

        validateBounds(minLat, maxLat, minLon, maxLon);

        return repository.findLatestPositionWithinBounds(minLat, maxLat, minLon, maxLon, limit);
    }
}
