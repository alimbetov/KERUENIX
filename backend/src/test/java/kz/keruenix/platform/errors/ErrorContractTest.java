package kz.keruenix.platform.errors;

import jakarta.validation.Valid;
import jakarta.validation.constraints.NotBlank;
import org.junit.jupiter.api.Test;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.setup.MockMvcBuilders;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RestController;

import static org.assertj.core.api.Assertions.assertThat;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.content;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.header;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

/** Standalone MVC tests: no database, tenant security or production CI is implied. */
class ErrorContractTest {
    private MockMvc mvc() {
        return MockMvcBuilders.standaloneSetup(new StubController())
                .setControllerAdvice(new ApiExceptionHandler(new ApiProblemFactory()))
                .addFilters(new RequestIdFilter())
                .build();
    }

    @Test
    void expectedCapacityConflictHasStableMachineCodeAndCorrelation() throws Exception {
        var result = mvc().perform(get("/test/capacity")
                        .header("X-Request-ID", "attacker-controlled\r\nInjected: yes"))
                .andExpect(status().isConflict())
                .andExpect(content().contentTypeCompatibleWith("application/problem+json"))
                .andExpect(jsonPath("$.code").value("KX-FLT-409-001"))
                .andExpect(jsonPath("$.status").value(409))
                .andExpect(jsonPath("$.retryable").value(false))
                .andExpect(jsonPath("$.type").value("urn:keruenix:problem:KX-FLT-409-001"))
                .andExpect(header().exists("X-Request-ID"))
                .andExpect(header().string("Cache-Control", "no-store"))
                .andReturn();

        String requestId = result.getResponse().getHeader("X-Request-ID");
        assertThat(requestId).isNotBlank();
        assertThat(requestId).doesNotContain("attacker");
        assertThat(result.getResponse().getContentAsString()).contains(requestId);
    }

    @Test
    void invalidBodyIsGenericAndDoesNotLeakParserDetails() throws Exception {
        mvc().perform(post("/test/validate")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("{not json"))
                .andExpect(status().isBadRequest())
                .andExpect(jsonPath("$.code").value("KX-GEN-400-001"))
                .andExpect(jsonPath("$.detail").value("The request could not be parsed or validated."));
    }

    @Test
    void validationErrorOmitsRejectedUserValues() throws Exception {
        var result = mvc().perform(post("/test/validate")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("{\"privateValue\":\"\"}"))
                .andExpect(status().isBadRequest())
                .andExpect(jsonPath("$.code").value("KX-GEN-400-002"))
                .andExpect(jsonPath("$.violations[0].field").value("privateValue"))
                .andReturn();

        assertThat(result.getResponse().getContentAsString()).doesNotContain("rejectedValue");
    }

    @Test
    void unknownFailureIsSafeGeneric500WithoutExceptionMessage() throws Exception {
        var result = mvc().perform(get("/test/unexpected"))
                .andExpect(status().isInternalServerError())
                .andExpect(jsonPath("$.code").value("KX-GEN-500-001"))
                .andReturn();
        assertThat(result.getResponse().getContentAsString()).doesNotContain("SQL SECRET");
        assertThat(result.getResponse().getContentAsString()).doesNotContain("IllegalStateException");
    }

    @Test
    void httpMethodViolationPreservesAllowAnd405() throws Exception {
        mvc().perform(get("/test/validate"))
                .andExpect(status().isMethodNotAllowed())
                .andExpect(jsonPath("$.code").value("KX-GEN-405-001"))
                .andExpect(header().exists("Allow"));
    }

    @RestController
    static class StubController {
        @GetMapping("/test/capacity")
        String capacity() {
            throw new DomainProblemException(ErrorCode.CAPACITY_CONFLICT);
        }

        @GetMapping("/test/unexpected")
        String unexpected() {
            throw new IllegalStateException("SQL SECRET credentials");
        }

        @PostMapping(path = "/test/validate", consumes = "application/json")
        String validate(@Valid @RequestBody Input input) {
            return "ok";
        }
    }

    record Input(@NotBlank String privateValue) {}
}
