package kz.keruenix.platform.errors;

import jakarta.servlet.http.HttpServletRequest;
import org.springframework.http.HttpStatusCode;
import org.springframework.http.ProblemDetail;
import org.springframework.stereotype.Component;

import java.net.URI;
import java.time.Instant;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

/** Single RFC 9457 factory shared by MVC and Spring Security filter responses. */
@Component
public final class ApiProblemFactory {
    public ProblemDetail create(ErrorCode code, HttpServletRequest request) {
        return create(code, code.status(), request, List.of());
    }

    public ProblemDetail create(
            ErrorCode code, HttpStatusCode httpStatus, HttpServletRequest request,
            List<Map<String, String>> violations) {
        String requestId = RequestIdFilter.requestId(request);
        ProblemDetail result = ProblemDetail.forStatusAndDetail(httpStatus, code.publicDetail());
        result.setTitle(code.title());
        result.setType(URI.create("urn:keruenix:problem:" + code.code()));
        result.setInstance(URI.create("urn:keruenix:incident:" + requestId));
        result.setProperty("code", code.code());
        result.setProperty("requestId", requestId);
        result.setProperty("retryable", code.retryable());
        result.setProperty("timestamp", Instant.now().toString());
        if (!violations.isEmpty()) {
            result.setProperty("violations", List.copyOf(violations));
        }
        return result;
    }

    /**
     * Filter-level security responses do not pass through Spring MVC's
     * ProblemDetail JSON mix-in. Flatten extensions explicitly.
     */
    public Map<String, Object> flatten(ProblemDetail problem) {
        Map<String, Object> json = new LinkedHashMap<>();
        json.put("type", problem.getType().toString());
        json.put("title", problem.getTitle());
        json.put("status", problem.getStatus());
        json.put("detail", problem.getDetail());
        json.put("instance", problem.getInstance().toString());
        if (problem.getProperties() != null) {
            json.putAll(problem.getProperties());
        }
        return json;
    }
}
