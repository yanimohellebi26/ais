package com.iem.backend.service;

import com.iem.backend.entity.User;
import com.iem.backend.entity.Vessel;
import com.iem.backend.exception.UserNotFoundException;
import com.iem.backend.repository.UserAccountRepository;
import com.iem.backend.repository.VesselRepository;
import jakarta.transaction.Transactional;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;
import org.springframework.web.server.ResponseStatusException;

@Service
public class VesselService {

    private final VesselRepository vesselRepository;
    private final UserAccountRepository userAccountRepository;

    public VesselService(VesselRepository vesselRepository, UserAccountRepository userAccountRepository) {
        this.vesselRepository = vesselRepository;
        this.userAccountRepository = userAccountRepository;
    }

    @Transactional
    public void relateUserToVessel(Integer userId, String mmsi) {
        User user = userAccountRepository.findById(userId)
                .orElseThrow(() -> new UserNotFoundException(userId));

        Vessel vessel = vesselRepository.findByMmsi(mmsi)
                .orElseThrow(() -> new ResponseStatusException(HttpStatus.NOT_FOUND, "Vessel found"));

        String roleName = user.getRole().getName();

        if ("OWNER".equalsIgnoreCase(roleName)) {
            boolean hasOwner = vessel.getUsers().stream()
                    .anyMatch(u -> "OWNER".equalsIgnoreCase(u.getRole().getName()));
            if (hasOwner) {
                throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "This vessel already has an OWNER");
            }
        }

        if (!vessel.getUsers().contains(user)) {
            vessel.getUsers().add(user);
            vesselRepository.save(vessel);
        }
    }

}
