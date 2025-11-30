package com.iem.backend.service;

import com.iem.backend.dto.positionVessel.PositionVesselRadiusProperties;
import com.iem.backend.entity.*;
import com.iem.backend.exception.ApiExceptions;
import com.iem.backend.exception.ApiExceptions.*;
import com.iem.backend.mapper.PositionVesselMapper;
import com.iem.backend.repository.PositionVesselRepository;

import org.locationtech.jts.geom.Point;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Pageable;
import org.springframework.security.access.AccessDeniedException;
import org.springframework.stereotype.Service;

import java.sql.Timestamp;
import java.time.Duration;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.util.*;
import java.util.stream.Collectors;

@Service
public class PositionVesselService {

    private final PositionVesselRepository positionVesselRepository;
    private final VesselService vesselService;
    private final PositionVesselMapper positionVesselMapper;

    private static final double MAX_RADIUS_KM = 500.0;
    private static final long WINDOW_HOURS = 12L;

    public PositionVesselService(PositionVesselRepository positionVesselRepository, VesselService vesselService, PositionVesselMapper positionVesselMapper) {
        this.positionVesselRepository = positionVesselRepository;
        this.vesselService = vesselService;
        this.positionVesselMapper = positionVesselMapper;
    }

    public List<PositionVessel> getPositionsByDateAndBounds(
            LocalDate dateStart, Optional<LocalDate> dateEnd,
            double minLat, double maxLat, double minLon, double maxLon, boolean distinct, int limit
    ) {
        validateBounds(minLat, maxLat, minLon, maxLon);

        LocalDate finalDateEnd = dateEnd.orElse(dateStart);
        if (finalDateEnd.isBefore(dateStart)) {
            throw new BadRequestException("End date must be after start date");
        }

        Timestamp start = Timestamp.valueOf(dateStart.atStartOfDay());
        Timestamp end = Timestamp.valueOf(finalDateEnd.atTime(23, 59, 59));

        if(distinct) {
            return positionVesselRepository.findByDateAndBoundsDistinct(start, end, minLat, maxLat, minLon, maxLon, limit);
        } else {
            return positionVesselRepository.findByDateAndBounds(start, end, minLat, maxLat, minLon, maxLon, limit);
        }

    }

    public List<PositionVessel> getUserVesselsPositionsByDateAndBounds(
            Integer userId,
            LocalDate dateStart, Optional<LocalDate> dateEnd,
            double minLat, double maxLat, double minLon, double maxLon, int limit
    ) {
        validateBounds(minLat, maxLat, minLon, maxLon);

        LocalDate finalDateEnd = dateEnd.orElse(dateStart);
        if (finalDateEnd.isBefore(dateStart)) {
            throw new BadRequestException("End date must be after start date");
        }

        Timestamp start = Timestamp.valueOf(dateStart.atStartOfDay());
        Timestamp end = Timestamp.valueOf(finalDateEnd.atTime(23, 59, 59));

        return positionVesselRepository.findByDateAndBoundsAndUserId(userId, start, end, minLat, maxLat, minLon, maxLon, limit);
    }

    public List<PositionVessel> getPositionsByIdAndOptionalDate(
            Integer vesselId, Optional<LocalDate> dateStartOpt, Optional<LocalDate> dateEndOpt, User currentUser
    ) {

        List<String> allowed = List.of("ADMIN","MARITIME_EXPERT","FINANCIAL_ANALYST");
        if (!allowed.contains(currentUser.getRole().getName())) {

            if(!vesselService.checkUserAccessToVessel(currentUser,vesselId)) {
                throw new ForbiddenException("Not allowed to access this position");
            }
        }

        List<PositionVessel> positionVessels;

        if (dateStartOpt.isEmpty() && dateEndOpt.isEmpty()) {
            // No date, all positions
            positionVessels = positionVesselRepository.findPositionVesselsByVesselId(vesselId);
        } else {

            LocalDate startDate = dateStartOpt.orElse(LocalDate.now());
            LocalDate endDate = dateEndOpt.orElse(startDate);

            if (endDate.isBefore(startDate)) {
                throw new BadRequestException("End date must be after or equal to start date");
            }

            Timestamp start = Timestamp.valueOf(startDate.atStartOfDay());
            Timestamp end = Timestamp.valueOf(endDate.atTime(23, 59, 59));

            positionVessels = positionVesselRepository.findPositionVesselsByVesselIdAndBaseDateTimeBetween(vesselId, start, end);
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

    public List<PositionVessel> getLatestPositions(CustomUserDetails currentUser, List<Integer> ids, int page, int size) {

        User user = currentUser.getUser();
        Role userRole = user.getRole();

        boolean isFullAccess = hasFullAccess(userRole);

        if (!isFullAccess) {
            if(!vesselService.checkUserAccessToVessels(user, ids)) {
                throw new ForbiddenException("Not allowed to access the vessels");
            };
        }

        Pageable pageable = PageRequest.of(page, size);

        Page<PositionVessel> positions;

        if (ids != null && !ids.isEmpty()) {
            positions = positionVesselRepository.findLatestPositionVesselsByIdIn(ids, pageable);
        } else {

            if (!isFullAccess) {
                List<Integer> userVesselIds = vesselService.getVesselIdsByUser(user.getId());

                if (userVesselIds == null || userVesselIds.isEmpty()) {
                    positions = Page.empty(pageable);
                } else {
                    positions = positionVesselRepository.findLatestPositionVesselsByIdIn(userVesselIds, pageable);
                }
                
            } else {
                positions = positionVesselRepository.findAll(pageable);
            }
        }

        return positions.getContent();
    }

    public List<PositionVessel> getLatestPositionsInBounds(
        CustomUserDetails currentUser,
        double minLat, double maxLat, double minLon, double maxLon,
        int limit
    ) {
        User user = currentUser.getUser();
        Role userRole = user.getRole();

        boolean isFullAccess = hasFullAccess(userRole);

        validateBounds(minLat, maxLat, minLon, maxLon);

        if (isFullAccess) {
            return positionVesselRepository.findLatestPositionWithinBounds(minLat, maxLat, minLon, maxLon, limit);
        } else {
            List<Integer> userVesselIds = vesselService.getVesselIdsByUser(user.getId());

            if (userVesselIds == null || userVesselIds.isEmpty()) {
                return Collections.emptyList();
            }

            return positionVesselRepository.findLatestPositionWithinBoundsForVessels(minLat, maxLat, minLon, maxLon, userVesselIds);
        }
    }

    public List<PositionVessel> getPositionsAroundVesselById(
            Integer vesselId,
            Optional<Object> dateOpt,
            Double radiusKmOpt,
            CustomUserDetails currentUser
    ){

        User user = currentUser.getUser();
        List<String> allowed = List.of("ADMIN","MARITIME_EXPERT","FINANCIAL_ANALYST");
        if (!allowed.contains(user.getRole().getName())) {
            if(!vesselService.checkUserAccessToVessel(user,vesselId)) {
                throw new ForbiddenException("Not allowed to access this position");
            }
        }

        double radiusKm = radiusKmOpt;
        if(radiusKm <= 0 || radiusKm > MAX_RADIUS_KM){
            throw new BadRequestException("Radius must be > 0 and <= "+ MAX_RADIUS_KM + " km");
        }

        PositionVessel targetPosition = resolveTargetPositionVessel(vesselId, dateOpt);
        Point targetGeom = targetPosition.getGeom();
        Timestamp targetTime = targetPosition.getBaseDateTime();
        if(targetGeom == null) throw new NotFoundException("Target vessel geom not found");

        double targetLat = targetGeom.getY();
        double targetLon = targetGeom.getX();

        Timestamp startDate = Timestamp.from(targetTime.toInstant().minus(Duration.ofHours(WINDOW_HOURS)));
        Timestamp endDate = Timestamp.from(targetTime.toInstant().plus(Duration.ofHours(WINDOW_HOURS)));

        return positionVesselRepository.findLastPositionsAround(
                targetLat,
                targetLon,
                radiusKm * 1000.0,
                startDate,
                endDate,
                vesselId
        );
    }

    public Map<Long, PositionVesselRadiusProperties> mapWithDistance(
            List<PositionVessel> vessels,
            Integer vesselId,
            Optional<Object> dateOpt
    ) {
        PositionVessel targetPosition = resolveTargetPositionVessel(vesselId, dateOpt);
        Point origin = targetPosition.getGeom();

        return vessels.stream().collect(Collectors.toMap(
                PositionVessel::getId,
                pv -> {
                    PositionVesselRadiusProperties dto = positionVesselMapper.toRadiusProperties(pv);
                    double distance = haversine(
                            origin.getY(), origin.getX(),
                            pv.getGeom().getY(), pv.getGeom().getX()
                    );
                    dto.setDistanceKm(distance);
                    return dto;
                }
        ));
    }


    private PositionVessel resolveTargetPositionVessel(Integer vesselId, Optional<Object> dateOpt){
        if(dateOpt.isEmpty()){
            return positionVesselRepository.findLatestPositionByVesselId(vesselId)
                    .orElseThrow(() -> new NotFoundException("No positions found for target vessel"));
        }

        Object date = dateOpt.get();

        if(date instanceof LocalDateTime ldt){
            Timestamp ts = Timestamp.valueOf(ldt);
            return positionVesselRepository.findPositionByVesselIdAndExactTime(vesselId, ts)
                    .orElseThrow(() -> new NotFoundException("No position found for vessel at the given time"));
        } else if (date instanceof LocalDate ld){
            Timestamp startDay = Timestamp.valueOf(ld.atStartOfDay());
            Timestamp endDay = Timestamp.valueOf(ld.atTime(23, 59, 59));
            return positionVesselRepository.findLastPositionInDay(vesselId, startDay, endDay)
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
