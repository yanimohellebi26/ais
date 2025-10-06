package com.iem.backend.service;

import com.iem.backend.dto.UpdateUserRequest;
import com.iem.backend.model.User;
import com.iem.backend.repository.UserRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.Optional;

@Service
public class UserService {

    @Autowired
    private UserRepository userRepository;

    @Transactional
    public User updateUser(UpdateUserRequest request) throws Exception {
        Optional<User> optionalUser = userRepository.findById(request.getId());
        if (optionalUser.isEmpty()) {
            throw new Exception("User not found");
        }

        User user = optionalUser.get();

        if (request.getPassword() != null && !request.getPassword().isEmpty()) {

            // FAIRE LE HASHAGE DU MOT DE PASSE
            user.setPasswordHash(request.getPassword());
        }

        if (request.getStatus() != null && !request.getStatus().isEmpty()) {
            user.setStatus(request.getStatus());
        }

        return userRepository.save(user);
    }
}
