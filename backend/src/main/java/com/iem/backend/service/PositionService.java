package com.iem.backend.service;

import java.util.List;
import java.util.stream.Collectors;

import org.springframework.security.access.AccessDeniedException;
import org.springframework.stereotype.Service;

import com.iem.backend.entity.PositionVessel;
import com.iem.backend.entity.Role;
import com.iem.backend.entity.User;
import com.iem.backend.entity.Vessel;
import com.iem.backend.repository.PositionVesselRepository;
import com.iem.backend.repository.VesselRepository;

import lombok.RequiredArgsConstructor;

@Service
@RequiredArgsConstructor
public class PositionService {

    private final PositionVesselRepository positionRepo;
    private final VesselRepository vesselRepo;

    public List<PositionVessel> getLatestPositions(User user, List<String> mmsiFilter) {

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
            return positionRepo.findLatestPositions(authorizedVesselIds);
        }

        if (authorizedVesselIds != null) {
            return positionRepo.findLatestPositions(authorizedVesselIds);
        }

        return positionRepo.findLatestPositions(filteredVesselIds);
    }
}
