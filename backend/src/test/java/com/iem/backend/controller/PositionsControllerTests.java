package com.iem.backend.controller;

import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.locationtech.jts.geom.GeometryFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.security.test.context.support.WithMockUser;
import org.springframework.test.context.TestPropertySource;
import org.springframework.test.web.servlet.MockMvc;

import com.fasterxml.jackson.databind.ObjectMapper;
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
@TestPropertySource(properties = {
        "spring.datasource.url=jdbc:h2:mem:testdb;DB_CLOSE_DELAY=-1;MODE=PostgreSQL",
        "spring.datasource.username=sa",
        "spring.datasource.password=",
        "spring.datasource.driver-class-name=org.h2.Driver",
        "spring.jpa.hibernate.ddl-auto=create-drop",
        "spring.jpa.show-sql=false"
})
public class PositionsControllerTests {

    @Autowired
    private MockMvc mockMvc;

    @Autowired
    private ObjectMapper objectMapper;

    @Autowired
    private RoleRepository roleRepository;

    @Autowired
    private UserRepository userRepository;

    @Autowired
    private VesselRepository vesselRepository;

    @Autowired
    private PositionVesselRepository positionRepository;

    private Role ownerRole;
    private Role maritimeRole;
    private User ownerUser;
    private User maritimeUser;
    private Vessel vessel1;
    private Vessel vessel2;

    private GeometryFactory geometryFactory = new GeometryFactory();

    @BeforeEach
    void setUp() {
        positionRepository.deleteAll();
        vesselRepository.deleteAll();
        userRepository.deleteAll();
        roleRepository.deleteAll();

        ownerRole = new Role();
        ownerRole.setName("OWNER");
        roleRepository.save(ownerRole);

        maritimeRole = new Role();
        maritimeRole.setName("MARITIME_EXPERT");
        roleRepository.save(maritimeRole);

        ownerUser = new User();
        ownerUser.setUsername("ownerUser");
        ownerUser.setRole(ownerRole);
        userRepository.save(ownerUser);

        maritimeUser = new User();
        maritimeUser.setUsername("maritimeUser");
        maritimeUser.setRole(maritimeRole);
        userRepository.save(maritimeUser);

        vessel1 = new Vessel();
        vessel1.setMmsi("111111111");
        vessel1.getUsers().add(ownerUser);
        vesselRepository.save(vessel1);

        vessel2 = new Vessel();
        vessel2.setMmsi("222222222");
        vesselRepository.save(vessel2);

        PositionVessel pos1 = new PositionVessel();
        pos1.setVesselId(vessel1.getId());
        pos1.setBaseDateTime(java.time.LocalDateTime.now());
        pos1.setSog(10.0);
        pos1.setCog(180.0);
        pos1.setHeading((short) 180);
        pos1.setGeom(geometryFactory.createPoint(new org.locationtech.jts.geom.Coordinate(5, 45)));
        positionRepository.save(pos1);

        PositionVessel pos2 = new PositionVessel();
        pos2.setVesselId(vessel2.getId());
        pos2.setBaseDateTime(java.time.LocalDateTime.now());
        pos2.setSog(12.0);
        pos2.setCog(90.0);
        pos2.setHeading((short) 90);
        pos2.setGeom(geometryFactory.createPoint(new org.locationtech.jts.geom.Coordinate(6, 46)));
        positionRepository.save(pos2);
    }

    @Test
    @WithMockUser(username = "ownerUser", roles = {"OWNER"})
    @DisplayName("Owner should see only his vessel")
    void ownerShouldSeeOwnVesselsOnly() throws Exception {
        mockMvc.perform(get("/api/v1/positions/latest")
                .contentType(MediaType.APPLICATION_JSON))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.length()").value(1))
            .andExpect(jsonPath("$[0].mmsi").value("111111111"));
    }
    
}
