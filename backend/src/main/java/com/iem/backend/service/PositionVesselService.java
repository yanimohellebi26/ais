package com.iem.backend.service;

import com.iem.backend.dto.PositionVesselDTO;
import com.iem.backend.entity.PositionVessel;
import com.iem.backend.entity.Role;
import com.iem.backend.entity.User;
import com.iem.backend.exception.ApiExceptions.*;
import com.iem.backend.exception.UserNotFoundException;
import com.iem.backend.repository.PositionVesselRepository;
import com.iem.backend.repository.UserRepository;
import com.iem.backend.repository.VesselRepository;

import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.security.access.AccessDeniedException;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.stereotype.Service;

import java.sql.Timestamp;
import java.time.LocalDate;
import java.util.List;
import java.util.Optional;

@Service
public class PositionVesselService {

    private final PositionVesselRepository repository;
    private final VesselRepository vesselRepo;
    private final UserRepository userRepo;

    private final VesselService vesselService;

    public PositionVesselService(PositionVesselRepository repository,VesselService vesselService, VesselRepository vesselRepo, UserRepository userRepo) {
        this.repository = repository;
        this.vesselService = vesselService;
        this.vesselRepo = vesselRepo;
        this.userRepo = userRepo;
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

    public List<PositionVesselDTO> getLatestPositions(UserDetails userDetails, List<String> mmsiFilter, Pageable pageable) {

        User user = userRepo.findByEmailIgnoreCase(userDetails.getUsername())
            .orElseThrow(() -> new UserNotFoundException(userDetails.getUsername()));

        List<Integer> authorizedVesselIds;
        
        Role userRole = user.getRole();

        switch (userRole.getName()) {
            case "OWNER", "CAPTAIN" -> {
                authorizedVesselIds = vesselRepo.findVesselIdsByUserId(user.getId());
            }

            case "MARITIME_EXPERT", "FINANCIAL_ANALYST" -> {
                authorizedVesselIds = null;
            }
        
            default -> throw new AccessDeniedException("Unauthorized Role");
        }

        List<Integer> filteredVesselIds = null;

        boolean filterCondition = mmsiFilter != null && !mmsiFilter.isEmpty();

        if (filterCondition) {
            filteredVesselIds = vesselRepo.findIdsByMmsi(mmsiFilter);

            if (authorizedVesselIds != null) {
                authorizedVesselIds.retainAll(filteredVesselIds);
            } else {
                authorizedVesselIds = filteredVesselIds;
            }
        }

        Page<PositionVessel> positions;

        if (authorizedVesselIds == null || authorizedVesselIds.isEmpty()) {
            positions = repository.findAll(pageable);
        } else { 
            positions = repository.findByVesselIds(authorizedVesselIds, filterCondition ? null : pageable);
        }

        return positions.getContent().stream()
            .map(pv -> new PositionVesselDTO(
                pv.getVessel().getMmsi(),
                pv.getBaseDateTime(),
                pv.getSog(),
                pv.getCog(),
                pv.getHeading(),
                pv.getStatus(),
                pv.getGeom() != null ? pv.getGeom().getCoordinate().y : null,
                pv.getGeom() != null ? pv.getGeom().getCoordinate().x : null
                ))
            .toList();
    }
}
