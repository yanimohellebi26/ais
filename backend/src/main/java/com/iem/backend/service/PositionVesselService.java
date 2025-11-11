package com.iem.backend.service;

import com.iem.backend.dto.positionVessel.VesselPositionRadiusDTO;
import com.iem.backend.entity.*;
import com.iem.backend.exception.ApiExceptions.*;
import com.iem.backend.repository.PositionVesselRepository;

import org.locationtech.jts.geom.Point;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.security.access.AccessDeniedException;
import org.springframework.stereotype.Service;

import java.sql.Timestamp;
import java.time.Duration;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.util.Collections;
import java.util.Comparator;
import java.util.List;
import java.util.Optional;

@Service
public class PositionVesselService {

    private final PositionVesselRepository repository;
    private final VesselService vesselService;

    private static final double DEFAULT_RADIUS_KM = 50.0;
    private static final double MAX_RADIUS_KM = 500.0;
    private static final long WINDOW_HOURS = 12L;

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

    private boolean hasFullAccess(Role role) {
        return switch (role.getName()) {
            case "ADMIN", "MARITIME_EXPERT", "FINANCIAL_ANALYST" -> true;
            case "OWNER", "CAPTAIN" -> false;
            default -> throw new AccessDeniedException("Unauthorized Role");
        };
    }

    public List<PositionVessel> getLatestPositions(CustomUserDetails customUserDetails, List<String> mmsisFilter, Pageable pageable) {

        User user = customUserDetails.getUser();      
        Role userRole = user.getRole();

        boolean isFullAccess = hasFullAccess(userRole);

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

        boolean isFullAccess = hasFullAccess(userRole);

        validateBounds(minLat, maxLat, minLon, maxLon);

        if (isFullAccess) {
            return repository.findLatestPositionWithinBounds(minLat, maxLat, minLon, maxLon, limit);
        } else {
            List<Integer> userVesselIds = vesselService.getVesselIdsByUser(user.getId());

            if (userVesselIds == null || userVesselIds.isEmpty()) {
                return Collections.emptyList();
            }

            return repository.findLatestPositionWithinBoundsForVessels(minLat, maxLat, minLon, maxLon, userVesselIds);
        }
    }

    public List<VesselPositionRadiusDTO> getPositionsAroundVesselByMmsi(
            String targetMmsi,
            Optional<Object> dateOpt,
            Optional<Double> radiusKmOpt,
            User currentUser
    ){
        Vessel targetVessel = vesselService.getVesselByMmsi(targetMmsi);
        Integer targetVesselId = targetVessel.getId();

        List<String> allowed = List.of("ADMIN","MARITIME_EXPERT","FINANCIAL_ANALYST");
        if (!allowed.contains(currentUser.getRole().getName())) {
            vesselService.checkUserHasAccessToVessel(currentUser,targetVesselId);
        }

        double radiusKm = radiusKmOpt.orElse(DEFAULT_RADIUS_KM);
        if(radiusKm <= 0 || radiusKm > MAX_RADIUS_KM){
            throw new BadRequestException("Radius must be > 0 and <= "+ MAX_RADIUS_KM + " km");
        }

        PositionVessel targetPosition = resolveTargetPositionVessel(targetVesselId, dateOpt);
        Point targetGeom = targetPosition.getGeom();
        Timestamp targetTime = targetPosition.getBaseDateTime();
        if(targetGeom == null) throw new NotFoundException("Target vessel geom not found");

        double targetLat = targetGeom.getY();
        double targetLon = targetGeom.getX();

        Timestamp startDate = Timestamp.from(targetTime.toInstant().minus(Duration.ofHours(WINDOW_HOURS)));
        Timestamp endDate = Timestamp.from(targetTime.toInstant().plus(Duration.ofHours(WINDOW_HOURS)));

        List<PositionVessel> allPositions = repository.findPositionsAround(
                targetLat,
                targetLon,
                radiusKm * 1000.0,
                startDate,
                endDate,
                targetVesselId
        );

        return allPositions.stream()
                .map(p -> new VesselPositionRadiusDTO(
                        p.getVessel().getMmsi(),
                        p.getGeom().getY(),
                        p.getGeom().getX(),
                        haversine(targetLat, targetLon, p.getGeom().getY(), p.getGeom().getX()),
                        p.getBaseDateTime()
                ))
                .sorted(Comparator.comparing(VesselPositionRadiusDTO::distanceKm))
                .toList();
    }

    private PositionVessel resolveTargetPositionVessel(Integer vesselId, Optional<Object> dateOpt){
        if(dateOpt.isEmpty()){
            return repository.findLatestPositionByVesselId(vesselId)
                    .orElseThrow(() -> new NotFoundException("No positions found for target vessel"));
        }

        Object date = dateOpt.get();

        if(date instanceof LocalDateTime ldt){
            Timestamp ts = Timestamp.valueOf(ldt);
            return repository.findPositionByVesselIdAndExactTime(vesselId, ts)
                    .orElseThrow(() -> new NotFoundException("No position found for vessel at the given time"));
        } else if (date instanceof LocalDate ld){
            Timestamp startDay = Timestamp.valueOf(ld.atStartOfDay());
            Timestamp endDay = Timestamp.valueOf(ld.atTime(23, 59, 59));
            return repository.findLastPositionInDay(vesselId, startDay, endDay)
                    .orElseThrow(() -> new NotFoundException("No position found for the vessel at the given day"));
        } else {
            throw new BadRequestException("Invalid date type");
        }
    }

    private static double haversine(double lat1, double lon1, double lat2, double lon2){
        final double R = 6371.0;
        double dLat = Math.toRadians(lat2 - lat1);
        double dLon = Math.toRadians(lon2 - lon1);
        lat1 = Math.toRadians(lat1);
        lat2 = Math.toRadians(lat2);

        double a = Math.pow(Math.sin(dLat / 2) , 2)
                + Math.cos(lat1) * Math.cos(lat2)
                * Math.pow(Math.sin(dLon / 2), 2);
        double c = 2 * Math.asin(Math.sqrt(a));
        return R * c;
    }

}
