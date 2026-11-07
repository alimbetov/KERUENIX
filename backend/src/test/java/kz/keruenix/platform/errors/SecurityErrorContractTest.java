package kz.keruenix.platform.errors;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.webmvc.test.autoconfigure.AutoConfigureMockMvc;
import org.springframework.test.web.servlet.MockMvc;

import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.content;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.header;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;
import org.springframework.security.test.context.support.WithMockUser;

/** Runs against the actual fail-closed servlet SecurityFilterChain. */
@SpringBootTest
@AutoConfigureMockMvc
class SecurityErrorContractTest {
    @Autowired MockMvc mvc;

    @Test
    void anonymousRequestGetsSameRfc9457ContractFromSecurityFilter() throws Exception {
        mvc.perform(get("/api/private"))
                .andExpect(status().isUnauthorized())
                .andExpect(content().contentTypeCompatibleWith("application/problem+json"))
                .andExpect(jsonPath("$.code").value("KX-AUTH-401-001"))
                .andExpect(jsonPath("$.status").value(401))
                .andExpect(header().string("WWW-Authenticate", "Bearer"))
                .andExpect(header().exists("X-Request-ID"));
    }

    @Test
    @WithMockUser
    void authenticatedButNotGrantedRequestIs403() throws Exception {
        mvc.perform(get("/api/private"))
                .andExpect(status().isForbidden())
                .andExpect(jsonPath("$.code").value("KX-AUTH-403-001"))
                .andExpect(jsonPath("$.status").value(403))
                .andExpect(header().exists("X-Request-ID"));
    }
}
