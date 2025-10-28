package com.iem.backend.service;

import com.iem.backend.dto.VesselResponseDto;
import com.iem.backend.entity.User;
import com.iem.backend.entity.Vessel;
import com.iem.backend.exception.UserNotFoundException;
import com.iem.backend.exception.VesselAlreadyOwnedException;
import com.iem.backend.exception.VesselNotFoundException;
import com.iem.backend.repository.UserRepository;
import com.iem.backend.repository.VesselRepository;
import jakarta.transaction.Transactional;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Pageable;
import org.springframework.data.domain.Sort;
import org.springframework.http.HttpStatus;
import org.springframework.security.access.AccessDeniedException;
import org.springframework.stereotype.Service;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.server.ResponseStatusException;

import java.sql.Timestamp;
import java.util.List;
import java.util.Optional;

@Service
public class VesselService {

    private final VesselRepository vesselRepository;
    private final UserRepository userRepository;

    public VesselService(VesselRepository vesselRepository, UserRepository userRepository) {
        this.vesselRepository = vesselRepository;
        this.userRepository = userRepository;
    }

    @Transactional
    public void relateUserToVessel(Integer userId, String mmsi) {
        User user = userRepository.findById(userId)
                .orElseThrow(() -> new UserNotFoundException(userId));

        Vessel vessel = vesselRepository.findByMmsi(mmsi)
                .orElseThrow(VesselNotFoundException::new);

        String roleName = user.getRole().getName();

        if ("OWNER".equalsIgnoreCase(roleName)) {
            boolean hasOwner = vessel.getUsers().stream()
                    .anyMatch(u -> "OWNER".equalsIgnoreCase(u.getRole().getName()));
            if (hasOwner) {
                throw new VesselAlreadyOwnedException();
            }
        }

        if (!vessel.getUsers().contains(user)) {
            vessel.getUsers().add(user);
            vesselRepository.save(vessel);
        }
    }

    public Page<VesselResponseDto> getAllVessels(int page, int size, String sortField, String sortDirection, String search) {
        Sort sort = sortDirection.equalsIgnoreCase("desc")
                ? Sort.by(sortField).descending()
                : Sort.by(sortField).ascending();

        Pageable pageable = PageRequest.of(page, size, sort);

        Page<Vessel> vesselsPage;

        if (search == null || search.isEmpty()) {
            vesselsPage = vesselRepository.findAll(pageable);
        } else if (search.matches("\\d+")) {
            vesselsPage = vesselRepository.searchByMmsiOrVesselName(search, pageable);
        } else {
            vesselsPage = vesselRepository.searchByVesselName(search, pageable);
        }
        
        return vesselsPage.map(VesselResponseDto::fromEntity);
    }

    public VesselResponseDto findById(Integer id){
        Vessel vessel = vesselRepository.findById(id).
            orElseThrow(()-> new VesselNotFoundException("Vessel not found with this id"));
        return VesselResponseDto.fromEntity(vessel);
    }
}
