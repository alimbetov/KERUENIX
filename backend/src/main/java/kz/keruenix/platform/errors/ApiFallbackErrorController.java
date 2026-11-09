package kz.keruenix.platform.errors;

import jakarta.servlet.RequestDispatcher;
import jakarta.servlet.http.HttpServletRequest;
import org.springframework.boot.webmvc.error.ErrorController;
import org.springframework.http.HttpStatusCode;
import org.springframework.http.MediaType;
import org.springframework.http.ProblemDetail;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;

/**
 * Covers servlet ERROR dispatches not handled by MVC Advice, without Boot's
 * default Map<String,Object> JSON or an HTML error page for API requests.
 */
@RestController
@RequestMapping("${spring.web.error.path:${error.path:/error}}")
public final class ApiFallbackErrorController implements ErrorController {
    private static final MediaType PROBLEM_JSON = MediaType.parseMediaType("application/problem+json");
    private final ApiProblemFactory problems;

    public ApiFallbackErrorController(ApiProblemFactory problems) {
        this.problems = problems;
    }

    @RequestMapping
    public ResponseEntity<ProblemDetail> error(HttpServletRequest request) {
        int status = statusOf(request);
        HttpStatusCode code = HttpStatusCode.valueOf(status);
        ErrorCode error = classify(status);
        ProblemDetail body = problems.create(error, code, request, List.of());
        return ResponseEntity.status(code)
                .contentType(PROBLEM_JSON)
                .header("Cache-Control", "no-store")
                .header(RequestIdFilter.HEADER, RequestIdFilter.requestId(request))
                .body(body);
    }

    private int statusOf(HttpServletRequest request) {
        Object attribute = request.getAttribute(RequestDispatcher.ERROR_STATUS_CODE);
        if (attribute instanceof Integer status && status >= 400 && status <= 599) {
            return status;
        }
        return 500;
    }

    private ErrorCode classify(int status) {
        return switch (status) {
            case 400 -> ErrorCode.BAD_REQUEST;
            case 401 -> ErrorCode.AUTHENTICATION_REQUIRED;
            case 403 -> ErrorCode.PERMISSION_DENIED;
            case 404 -> ErrorCode.RESOURCE_NOT_FOUND;
            case 405 -> ErrorCode.METHOD_NOT_ALLOWED;
            case 415 -> ErrorCode.UNSUPPORTED_MEDIA_TYPE;
            case 429 -> ErrorCode.RATE_LIMITED;
            case 503 -> ErrorCode.UPSTREAM_UNAVAILABLE;
            default -> status >= 500 ? ErrorCode.INTERNAL_ERROR : ErrorCode.FRAMEWORK_HTTP_ERROR;
        };
    }
}
