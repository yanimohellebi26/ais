package com.iem.backend.service;

import com.iem.backend.entity.User;
import com.iem.backend.repository.UserAccountRepository;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.security.core.userdetails.UserDetailsService;
import org.springframework.security.core.userdetails.UsernameNotFoundException;
import org.springframework.stereotype.Service;

import java.util.Collections;

@Service
public class UserService implements UserDetailsService {

    private final UserAccountRepository userAccountRepository;

    /**
     * Initializes the service with the user account repository.
     *
     * @param userAccountRepository repository for accessing user data
     */
    public UserService(UserAccountRepository userAccountRepository) {
        this.userAccountRepository = userAccountRepository;
    }

    /**
     * Loads a user by their email address for authentication.
     *
     * @param email user's email
     * @return user details for authentication
     * @throws UsernameNotFoundException if no user is found with the given email
     */
    @Override
    public UserDetails loadUserByUsername(String email){

        User user = this.userAccountRepository.findByEmailIgnoreCase(email).orElseThrow(() -> new UsernameNotFoundException("User Not Found with username: " + email));
        return new org.springframework.security.core.userdetails.User(
                user.getEmail(),
                user.getPasswordHash(),
                Collections.emptyList()
        );
    }
}
