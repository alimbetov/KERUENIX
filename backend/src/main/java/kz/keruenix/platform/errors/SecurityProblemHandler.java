package kz.keruenix.platform.errors;

import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import org.springframework.http.ProblemDetail;
import org.springframework.security.access.AccessDeniedException;
import org.springframework.security.core.AuthenticationException;
import org.springframework.security.web.AuthenticationEntryPoint;
import org.springframework.security.web.access.AccessDeniedHandler;
import org.springframework.stereotype.Component;
import tools.jackson.databind.json.JsonMapper;

import java.io.IOException;

/**
 * Servlet Security failures happen before @RestControllerAdvice.
 * Reuse the same factory and explicit RFC 9457 top-level extension serialization.
 */
@Component
public final class SecurityProblemHandler implements AuthenticationEntryPoint, AccessDeniedHandler {
    private final ApiProblemFactory problems;
    private final JsonMapper json;

    public SecurityProblemHandler(ApiProblemFactory problems, JsonMapper json) {
        this.problems = problems;
        this.json = json;
    }

    @Override
    public void commence(HttpServletRequest request, HttpServletResponse response,
                         AuthenticationException exception) throws IOException {
        // The Bearer challenge becomes meaningful once a verified JWT resource server is installed.
        if (!response.isCommitted()) {
            response.setHeader("WWW-Authenticate", "Bearer");
        }
        write(ErrorCode.AUTHENTICATION_REQUIRED, request, response);
    }

    @Override
    public void handle(HttpServletRequest request, HttpServletResponse response,
                       AccessDeniedException exception) throws IOException {
        write(ErrorCode.PERMISSION_DENIED, request, response);
    }

    private void write(ErrorCode code, HttpServletRequest request,
                       HttpServletResponse response) throws IOException {
        if (response.isCommitted()) {
            return; // Never attempt to append a second JSON response to a committed stream.
        }
        ProblemDetail problem = problems.create(code, request);
        response.setStatus(code.status().value());
        response.setContentType("application/problem+json");
        response.setHeader(RequestIdFilter.HEADER, RequestIdFilter.requestId(request));
        response.setHeader("Cache-Control", "no-store");
        json.writeValue(response.getOutputStream(), problems.flatten(problem));
    }
}
