package com.iem.backend.service;

import java.util.List;
import java.util.stream.Collectors;

import org.springframework.security.access.AccessDeniedException;
import org.springframework.stereotype.Service;

import com.iem.backend.dto.PositionVesselDTO;
import com.iem.backend.entity.PositionVessel;
import com.iem.backend.entity.Role;
import com.iem.backend.entity.User;
import com.iem.backend.entity.Vessel;
import com.iem.backend.repository.PositionVesselRepository;
import com.iem.backend.repository.VesselRepository;

@Service
public class PositionService {

    private final PositionVesselRepository positionRepo;
    private final VesselRepository vesselRepo;

    public PositionService(PositionVesselRepository positionRepo, VesselRepository vesselRepo) {
        this.positionRepo = positionRepo;
        this.vesselRepo = vesselRepo;
    }

    public List<PositionVesselDTO> getLatestPositions(User user, List<String> mmsiFilter) {

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
            filteredVesselIds = vesselRepo.findAll().stream()
                .filter(v -> mmsiFilter.contains(v.getMmsi()))
                .map(Vessel::getId)
                .collect(Collectors.toList());
        }

        if (authorizedVesselIds != null && filteredVesselIds != null) {
            authorizedVesselIds.retainAll(filteredVesselIds);
            filteredVesselIds = authorizedVesselIds;
        } else if (authorizedVesselIds != null) {
            filteredVesselIds = authorizedVesselIds;
        }

        List<PositionVessel> positions = positionRepo.findLatestPositions(filteredVesselIds);

        return positions.stream()
            .map(pv -> new PositionVesselDTO(
                pv.getVessel().getMmsi(),
                pv.getBaseDateTime(),
                pv.getSog(),
                pv.getCog(),
                pv.getHeading(),
                pv.getStatusId(),
                pv.getGeom() != null ? pv.getGeom().getCoordinate().y : null,
                pv.getGeom() != null ? pv.getGeom().getCoordinate().x : null
                ))
            .collect(Collectors.toList());
    }
}
