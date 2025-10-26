package com.iem.backend.controller;

import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import java.sql.Timestamp;
import java.util.ArrayList;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.locationtech.jts.geom.Coordinate;
import org.locationtech.jts.geom.GeometryFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.security.test.context.support.WithMockUser;
import org.springframework.test.web.servlet.MockMvc;

import com.iem.backend.entity.PositionVessel;
import com.iem.backend.entity.Role;
import com.iem.backend.entity.User;
import com.iem.backend.entity.Vessel;
import com.iem.backend.repository.PositionVesselRepository;
import com.iem.backend.repository.RoleRepository;
import com.iem.backend.repository.UserRepository;
import com.iem.backend.repository.VesselRepository;

import org.springframework.http.MediaType;

@SpringBootTest
@AutoConfigureMockMvc
public class PositionsControllerTest {

    @Autowired
    private MockMvc mockMvc;

    @Autowired
    private RoleRepository roleRepository;

    @Autowired
    private UserRepository userRepository;

    @Autowired
    private VesselRepository vesselRepository;

    @Autowired
    private PositionVesselRepository positionRepository;

    @Autowired
    private PasswordEncoder passwordEncoder;

    private Role ownerRole;
    private Role maritimeRole;
    private Role captainRole;
    private Role financialRole;

    private User ownerUser;
    private User maritimeUser;
    private User captainUser;
    private User financialUser;

    private Vessel vessel1;
    private Vessel vessel2;

    private GeometryFactory geometryFactory = new GeometryFactory();

    private void createRoles() {
        ownerRole = new Role();
        ownerRole.setName("OWNER");
        roleRepository.save(ownerRole);

        maritimeRole = new Role();
        maritimeRole.setName("MARITIME_EXPERT");
        roleRepository.save(maritimeRole);

        captainRole = new Role(); 
        captainRole.setName("CAPTAIN"); 
        roleRepository.save(captainRole);

        financialRole = new Role(); 
        financialRole.setName("FINANCIAL_ANALYST"); 
        roleRepository.save(financialRole);
    }

    private void createUsers() {
        ownerUser = new User();
        ownerUser.setUsername("ownerUser");
        ownerUser.setEmail("owner@example.com");
        ownerUser.setPasswordHash(passwordEncoder.encode("Password@123"));
        ownerUser.setRole(ownerRole);
        ownerUser.setFileUploads(new ArrayList<>());
        userRepository.save(ownerUser);

        maritimeUser = new User();
        maritimeUser.setUsername("maritimeUser");
        maritimeUser.setEmail("maritime@example.com");
        maritimeUser.setPasswordHash(passwordEncoder.encode("Password@456"));
        maritimeUser.setRole(maritimeRole);
        maritimeUser.setFileUploads(new ArrayList<>());
        userRepository.save(maritimeUser);

        captainUser = new User();
        captainUser.setUsername("captainUser");
        captainUser.setEmail("captain@example.com");
        captainUser.setPasswordHash(passwordEncoder.encode("Password@789"));
        captainUser.setRole(captainRole);
        captainUser.setFileUploads(new ArrayList<>());
        userRepository.save(captainUser);

        financialUser = new User();
        financialUser.setUsername("financialUser");
        financialUser.setEmail("financial@example.com");
        financialUser.setPasswordHash(passwordEncoder.encode("Password@167"));
        financialUser.setRole(financialRole);
        financialUser.setFileUploads(new ArrayList<>());
        userRepository.save(financialUser);
    }

    private void createVessels() {
        vessel1 = new Vessel();
        vessel1.setMmsi("111111111");
        vessel1.setCreatedAt(new Timestamp(System.currentTimeMillis()));
        vessel1.setBaseDateTime(new Timestamp(System.currentTimeMillis()));
        vessel1.getUsers().add(ownerUser);
        vessel1.getUsers().add(captainUser);
        vesselRepository.save(vessel1);

        vessel2 = new Vessel();
        vessel2.setMmsi("222222222");
        vessel2.setCreatedAt(new Timestamp(System.currentTimeMillis()));
        vessel2.setBaseDateTime(new Timestamp(System.currentTimeMillis()));
        vesselRepository.save(vessel2);
    }

    @BeforeEach
    void setUp() {
        positionRepository.deleteAll();
        vesselRepository.deleteAll();
        userRepository.deleteAll();
        roleRepository.deleteAll();

        createRoles();
        createUsers();
        createVessels();

        PositionVessel pos1 = new PositionVessel();
        pos1.setVesselId(vessel1.getId());
        pos1.setBaseDateTime(new Timestamp(System.currentTimeMillis()));
        pos1.setSog(10.0);
        pos1.setCog(180.0);
        pos1.setHeading((short) 180);
        pos1.setGeom(geometryFactory.createPoint(new Coordinate(5, 45)));
        positionRepository.save(pos1);

        PositionVessel pos2 = new PositionVessel();
        pos2.setVesselId(vessel2.getId());
        pos2.setBaseDateTime(new Timestamp(System.currentTimeMillis()));
        pos2.setSog(12.0);
        pos2.setCog(90.0);
        pos2.setHeading((short) 90);
        pos2.setGeom(geometryFactory.createPoint(new Coordinate(6, 46)));
        positionRepository.save(pos2);
    }

    @Test
    @WithMockUser(username = "owner@example.com", roles = {"OWNER"})
    @DisplayName("Owner should see only his vessel")
    void ownerShouldSeeOwnVesselsOnly() throws Exception {
        System.out.println(positionRepository.findAll());
        mockMvc.perform(get("/api/v1/positions/latest")
                .contentType(MediaType.APPLICATION_JSON))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.length()").value(1))
            .andExpect(jsonPath("$[0].mmsi").value("111111111"));
    }

    @Test
    @WithMockUser(username = "maritime@example.com", roles = {"MARITIME_EXPERT"})
    @DisplayName("Maritime sees all vessels")
    void maritimeSeesAllVessels() throws Exception {
        mockMvc.perform(get("/api/v1/positions/latest")
                .contentType(MediaType.APPLICATION_JSON))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.length()").value(2));
    }

    @Test
    @WithMockUser(username = "financial@example.com", roles = {"FINANCIAL_ANALYST"})
    @DisplayName("Financial sees all vessels")
    void financialSeesAllVessels() throws Exception {
        mockMvc.perform(get("/api/v1/positions/latest").contentType(MediaType.APPLICATION_JSON))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.length()").value(2));
    }
    
    @Test
    @WithMockUser(username = "captain@example.com", roles = {"CAPTAIN"})
    @DisplayName("Captain sees only their vessels")
    void captainSeesOwnVessels() throws Exception {
        mockMvc.perform(get("/api/v1/positions/latest").contentType(MediaType.APPLICATION_JSON))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.length()").value(1))
            .andExpect(jsonPath("$[0].mmsi").value("111111111"));
    }
    
    @Test
    @WithMockUser(username = "owner@example.com", roles = {"OWNER"})
    @DisplayName("Owner can filter vessels by MMSI")
    void ownerCanFilterByMmsi() throws Exception {
        mockMvc.perform(get("/api/v1/positions/latest")
                .param("mmsi", "111111111")
                .contentType(MediaType.APPLICATION_JSON))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.length()").value(1))
            .andExpect(jsonPath("$[0].mmsi").value("111111111"));

        mockMvc.perform(get("/api/v1/positions/latest")
                .param("mmsi", "222222222")
                .contentType(MediaType.APPLICATION_JSON))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.length()").value(0));
    }
}
