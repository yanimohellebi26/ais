package com.iem.backend.service;
import com.iem.backend.dto.RequestVesselDto;
import com.iem.backend.dto.VesselResponseDto;
import com.iem.backend.entity.User;
import com.iem.backend.entity.Vessel;
import com.iem.backend.exception.UserAccessDeniedException;
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
import org.springframework.stereotype.Service;

import java.security.Principal;
import java.sql.Timestamp;
import java.util.List;

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

    public RequestVesselDto createVessel(RequestVesselDto dto){
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
        
        return RequestVesselDto.fromEntity(saved);
    }

    public VesselResponseDto updateVessel(Integer id,VesselResponseDto dto,Principal principal){
        Vessel vessel = vesselRepository.findById(id).
            orElseThrow(()-> new VesselNotFoundException("Vessel not found with this id"));

        User currentUser = userRepository.findByEmailIgnoreCase(principal.getName()).
            orElseThrow(()-> new UserNotFoundException());

        if(!currentUser.getRole().getName().equals("ADMIN")){
            boolean ownVessel = vesselRepository.existsByIdAndUserId(id,currentUser.getId());
            if (!ownVessel){
                throw new UserAccessDeniedException("You are not allowed to update this Vessel");
            }
        }

        if (dto.mmsi() != null && !dto.mmsi().isBlank()) vessel.setMmsi(dto.mmsi());
        if (dto.imo() != null && !dto.imo().isBlank()) vessel.setImo(dto.imo());
        if (dto.vesselName() != null && !dto.vesselName().isBlank()) vessel.setVesselName(dto.vesselName());
        if (dto.callSign() != null && !dto.callSign().isBlank()) vessel.setCallSign(dto.callSign());
        if (dto.length() != null) vessel.setLength(dto.length());
        if (dto.width() != null) vessel.setWidth(dto.width());
        if (dto.draft() != null) vessel.setDraft(dto.draft());
        if (dto.transceiverClass() != null) vessel.setTransceiverClass(dto.transceiverClass());
        if (dto.locked() != null) vessel.setLocked(dto.locked());
        if (dto.baseDateTime() != null) vessel.setBaseDateTime(dto.baseDateTime());
        vessel.setLastUpdate(new Timestamp(System.currentTimeMillis()));
        
        Vessel updated = vesselRepository.save(vessel);   
        
        return VesselResponseDto.fromEntity(updated);
    }

    public void deleteVessel(Integer id){
        Vessel vessel = vesselRepository.findById(id).
            orElseThrow(()-> new VesselNotFoundException("Vessel not found with this id"));

        vesselRepository.delete(vessel);
    }

    public List<VesselResponseDto> getVesselsByUserID(int userId){
        return vesselRepository.findByUserId(userId).stream().map(VesselResponseDto::fromEntity).toList();
    }

    
}

