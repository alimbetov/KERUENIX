package kz.keruenix.platform.errors;

import jakarta.servlet.RequestDispatcher;
import org.junit.jupiter.api.Test;
import org.springframework.mock.web.MockHttpServletRequest;

import static org.assertj.core.api.Assertions.assertThat;

class FallbackErrorControllerTest {
    private final ApiFallbackErrorController controller =
            new ApiFallbackErrorController(new ApiProblemFactory());

    @Test
    void missingResourceUsesSameSafeProblemSchema() {
        var request = new MockHttpServletRequest("GET", "/api/hidden-order/secret");
        request.setAttribute(RequestDispatcher.ERROR_STATUS_CODE, 404);

        var result = controller.error(request);

        assertThat(result.getStatusCode().value()).isEqualTo(404);
        assertThat(result.getBody()).isNotNull();
        assertThat(result.getBody().getProperties().get("code")).isEqualTo("KX-GEN-404-001");
        assertThat(result.getBody().getDetail()).doesNotContain("secret");
        assertThat(result.getHeaders().getFirst("Cache-Control")).isEqualTo("no-store");
    }

    @Test
    void absentOrInvalidServletStatusIsSafe500() {
        var request = new MockHttpServletRequest("GET", "/error");
        request.setAttribute(RequestDispatcher.ERROR_STATUS_CODE, "unexpected");

        var result = controller.error(request);

        assertThat(result.getStatusCode().value()).isEqualTo(500);
        assertThat(result.getBody()).isNotNull();
        assertThat(result.getBody().getProperties().get("code")).isEqualTo("KX-GEN-500-001");
        assertThat(result.getBody().getDetail()).doesNotContain("unexpected");
    }

    @Test
    void unknownFourHundredStatusIsPreservedWithoutMislabelingAs400() {
        var request = new MockHttpServletRequest("GET", "/error");
        request.setAttribute(RequestDispatcher.ERROR_STATUS_CODE, 406);

        var result = controller.error(request);

        assertThat(result.getStatusCode().value()).isEqualTo(406);
        assertThat(result.getBody().getStatus()).isEqualTo(406);
        assertThat(result.getBody().getProperties().get("code")).isEqualTo("KX-GEN-000-001");
    }
}
