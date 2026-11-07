package kz.keruenix.platform.errors;

import jakarta.servlet.http.HttpServletRequest;
import org.junit.jupiter.api.Test;
import org.springframework.http.ProblemDetail;
import org.springframework.mock.web.MockHttpServletRequest;

import java.util.Arrays;
import java.util.Map;
import java.util.stream.Collectors;

import static org.assertj.core.api.Assertions.assertThat;

/**
 * Contract invariants only. The canonical JSON catalog must be reviewed at
 * the same time as this enum; implementation tests do not replace business signoff.
 */
class ErrorCodeCatalogTest {
    private final ApiProblemFactory problems = new ApiProblemFactory();

    @Test
    void errorCodesAreUniqueAndCarryExpectedHttpStatus() {
        var codes = Arrays.stream(ErrorCode.values()).map(ErrorCode::code).toList();
        assertThat(codes).doesNotHaveDuplicates();

        for (ErrorCode error : ErrorCode.values()) {
            String encoded = error.code().split("-")[2];
            if (!"000".equals(encoded)) {
                assertThat(error.status().value()).isEqualTo(Integer.parseInt(encoded));
            }
            assertThat(error.code()).startsWith("KX-");
            assertThat(error.publicDetail()).isNotBlank();
        }
    }

    @Test
    void factoryProducesStableProblemTypeAndOpaqueRequestId() {
        HttpServletRequest request = new MockHttpServletRequest("GET", "/api/private/secret-order-id");
        ProblemDetail result = problems.create(ErrorCode.RESOURCE_NOT_FOUND, request);
        Map<String, Object> json = problems.flatten(result);

        assertThat(json.get("code")).isEqualTo("KX-GEN-404-001");
        assertThat(json.get("status")).isEqualTo(404);
        assertThat(json.get("type")).isEqualTo("urn:keruenix:problem:KX-GEN-404-001");
        assertThat(json.get("requestId")).isInstanceOf(String.class);
        assertThat(json.get("instance").toString()).contains(json.get("requestId").toString());
        assertThat(json.values().stream().map(String::valueOf).collect(Collectors.joining(" ")))
                .doesNotContain("secret-order-id");
    }

    @Test
    void protectedResourceAndMissingResourceHaveSamePublicText() {
        // Callers must use the SAME error code for foreign and nonexistent
        // resources. The reason for hiding the resource is internal audit only.
        var request = new MockHttpServletRequest("GET", "/api/private");
        var absent = problems.flatten(problems.create(ErrorCode.RESOURCE_NOT_FOUND, request));
        var foreign = problems.flatten(problems.create(ErrorCode.RESOURCE_NOT_FOUND, request));
        assertThat(foreign.get("code")).isEqualTo(absent.get("code"));
        assertThat(foreign.get("detail")).isEqualTo(absent.get("detail"));
        assertThat(foreign.get("status")).isEqualTo(absent.get("status"));
    }
}
