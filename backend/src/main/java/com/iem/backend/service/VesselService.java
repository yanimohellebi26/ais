package com.iem.backend.service;

import com.iem.backend.entity.User;
import com.iem.backend.entity.Vessel;
import com.iem.backend.exception.UserNotFoundException;
import com.iem.backend.exception.VesselAlreadyOwnedException;
import com.iem.backend.exception.VesselNotFoundException;
import com.iem.backend.repository.UserRepository;
import com.iem.backend.repository.VesselRepository;
import jakarta.transaction.Transactional;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;
import org.springframework.web.server.ResponseStatusException;

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

}
