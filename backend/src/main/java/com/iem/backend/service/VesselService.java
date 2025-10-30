package com.iem.backend.service;

import com.iem.backend.dto.VesselResponseDto;
import com.iem.backend.entity.User;
import com.iem.backend.entity.Vessel;
import com.iem.backend.entity.VesselType;
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

    public VesselResponseDto createVessel(VesselResponseDto dto){
        if (dto == null) {
            throw new IllegalArgumentException("Vessel data cannot be null");
        }

        if (dto.mmsi() == null || dto.mmsi().isBlank()) {
            throw new IllegalArgumentException("MMSI is required");
        }

        if (dto.imo() == null || dto.imo().isBlank()) {
            throw new IllegalArgumentException("IMO is required");
        }

        if (dto.vesselName() == null || dto.vesselName().isBlank()) {
            throw new IllegalArgumentException("Vessel name is required");
        }

        if (dto.callSign() == null || dto.callSign().isBlank()) {
            throw new IllegalArgumentException("Call sign is required");
        }

        if (dto.transceiverClass() == null) {
            throw new IllegalArgumentException("Transceiver class is required");
        }

        Vessel vessel = new Vessel();
        vessel.setMmsi(dto.mmsi());
        vessel.setImo(dto.imo());
        vessel.setVesselName(dto.vesselName());
        vessel.setCallSign(dto.callSign());
        vessel.setLength(dto.length());
        vessel.setWidth(dto.width());
        vessel.setDraft(dto.draft());
        vessel.setTransceiverClass(dto.transceiverClass());
        vessel.setLocked(dto.locked() != null ? dto.locked() : false);
        vessel.setCreatedAt(new Timestamp(System.currentTimeMillis()));
        vessel.setLastUpdate(new Timestamp(System.currentTimeMillis()));
        vessel.setBaseDateTime(dto.baseDateTime() != null ? dto.baseDateTime() : new Timestamp(System.currentTimeMillis()));

        Vessel saved = vesselRepository.save(vessel);
        
        return VesselResponseDto.fromEntity(saved);
    }
}

