package kz.keruenix.platform.security;

import java.util.Objects;
import java.util.UUID;

import org.springframework.security.access.AccessDeniedException;
import org.springframework.security.core.Authentication;
import org.springframework.security.oauth2.server.resource.authentication.JwtAuthenticationToken;

/**
 * FOUND-03/08/11: scope selection from an authenticated Spring Security JWT
 * plus an authoritative server-side membership/grant source. A signed tenant_id
 * claim is NOT a grant. CustomerAccount scope must be rechecked per operation.
 *
 * Production still has SecurityConfig denyAll; PR-02/03 will implement the
 * persistent verified grant source. NEVER instantiate this with "always true"
 * and NEVER derive privileges only from caller-supplied UUIDs or JWT claims.
 */
public final class TenantScopeAuthorization {
    @FunctionalInterface
    public interface VerifiedGrantSource {
        boolean canAccess(String subject, UUID tenantId, UUID customerAccountId);
    }

    public record Scope(String subject, UUID tenantId, UUID customerAccountId) {}

    private final VerifiedGrantSource grants;

    public TenantScopeAuthorization(VerifiedGrantSource grants) {
        this.grants = Objects.requireNonNull(grants, "grants");
    }

    public Scope authorize(Authentication authentication, UUID requestedTenant,
                           UUID requestedAccount, String tenantHeader, UUID tenantInBody) {
        if (!(authentication instanceof JwtAuthenticationToken jwtAuth)
                || !jwtAuth.isAuthenticated()) {
            throw new AccessDeniedException("Verified JWT authentication required");
        }
        if (requestedTenant == null || requestedAccount == null) {
            throw new AccessDeniedException("Missing tenant/customer resource scope");
        }
        String subject = jwtAuth.getToken().getSubject();
        if (subject == null || subject.isBlank()) {
            throw new AccessDeniedException("Verified actor subject required");
        }
        String selected = requestedTenant.toString();
        if ((tenantHeader != null && !selected.equals(tenantHeader))
                || (tenantInBody != null && !requestedTenant.equals(tenantInBody))) {
            throw new AccessDeniedException("Tenant selector conflicts with resource scope");
        }
        // The JWT has already passed signature/issuer/audience/expiry validation
        // inside the Spring Security resource server authentication filter.
        // The independent grant source MUST verify actor and selected account.
        if (!grants.canAccess(subject, requestedTenant, requestedAccount)) {
            throw new AccessDeniedException("No current membership or customer grant");
        }
        return new Scope(subject, requestedTenant, requestedAccount);
    }
}
