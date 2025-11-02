package com.iem.backend.service;

import java.util.List;

import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.security.access.AccessDeniedException;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.stereotype.Service;

import com.iem.backend.dto.PositionVesselDTO;
import com.iem.backend.entity.LatestPosition;
import com.iem.backend.entity.Role;
import com.iem.backend.entity.User;
import com.iem.backend.entity.Vessel;
import com.iem.backend.exception.UserNotFoundException;
import com.iem.backend.repository.PositionVesselRepository;
import com.iem.backend.repository.UserRepository;
import com.iem.backend.repository.VesselRepository;

@Service
public class PositionService {

    private final PositionVesselRepository positionRepo;
    private final VesselRepository vesselRepo;
    private final UserRepository userRepo;

    public PositionService(PositionVesselRepository positionRepo, VesselRepository vesselRepo, UserRepository userRepo) {
        this.positionRepo = positionRepo;
        this.vesselRepo = vesselRepo;
        this.userRepo = userRepo;

    }

    public Page<PositionVesselDTO> getLatestPositions(UserDetails userDetails, List<String> mmsiFilter, Pageable pageable) {

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
        if (mmsiFilter != null && !mmsiFilter.isEmpty()) {
            filteredVesselIds = vesselRepo.findIdsByMmsi(mmsiFilter);

            if (authorizedVesselIds != null) {
                authorizedVesselIds.retainAll(filteredVesselIds);
            } else {
                authorizedVesselIds = filteredVesselIds;
            }
        }

        Page<LatestPosition> positions;

        if (authorizedVesselIds == null || authorizedVesselIds.isEmpty()) {
            positions = positionRepo.findAll(pageable);
        } else { 
            positions = positionRepo.findByVesselIds(authorizedVesselIds, pageable);
        }

        return positions
            .map(pv -> new PositionVesselDTO(
                pv.getVessel().getMmsi(),
                pv.getBaseDateTime(),
                pv.getSog(),
                pv.getCog(),
                pv.getHeading(),
                pv.getStatusId(),
                pv.getGeom() != null ? pv.getGeom().getCoordinate().y : null,
                pv.getGeom() != null ? pv.getGeom().getCoordinate().x : null
                ));
    }
}
