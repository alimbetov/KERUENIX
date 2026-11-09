package kz.keruenix.platform.security;

import java.time.Instant;
import java.util.Set;
import java.util.UUID;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.atomic.AtomicInteger;

import org.junit.jupiter.api.Test;
import org.springframework.security.access.AccessDeniedException;
import org.springframework.security.authentication.TestingAuthenticationToken;
import org.springframework.security.oauth2.jwt.Jwt;
import org.springframework.security.oauth2.server.resource.authentication.JwtAuthenticationToken;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

/**
 * Direct tests of the EXISTING production grant boundary.
 * These are NOT tests of any CustomerAccount cache or background worker.
 * See docs/60-customer-account-cache-jobs-security-contract.md.
 */
class TenantScopeAuthorizationBoundaryTest {
    private static final UUID TENANT_A =
            UUID.fromString("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa");
    private static final UUID TENANT_B =
            UUID.fromString("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb");
    private static final UUID ACCOUNT_X =
            UUID.fromString("11111111-1111-1111-1111-111111111111");
    private static final UUID ACCOUNT_Y =
            UUID.fromString("22222222-2222-2222-2222-222222222222");

    private static JwtAuthenticationToken actor(String subject) {
        // Boundary unit test: JWT authentication is constructed as if it
        // had already passed the resource-server verifier. Signature validation
        // belongs to separate HTTP integration tests.
        var jwt = Jwt.withTokenValue("test-only")
                .header("alg", "RS256").subject(subject)
                .issuedAt(Instant.now().minusSeconds(2))
                .expiresAt(Instant.now().plusSeconds(60))
                .claim("tenant_id", TENANT_B.toString())
                .build();
        return new JwtAuthenticationToken(jwt);
    }

    @Test
    void aCachedScopeIsNotAReusableGrantAfterRevocation() {
        Set<String> authorized = ConcurrentHashMap.newKeySet();
        authorized.add("alice");
        AtomicInteger checks = new AtomicInteger();
        var gate = new TenantScopeAuthorization((subject, tenant, account) -> {
            checks.incrementAndGet();
            return authorized.contains(subject)
                    && TENANT_A.equals(tenant) && ACCOUNT_X.equals(account);
        });
        var token = actor("alice");
        var issuedScope = gate.authorize(token, TENANT_A, ACCOUNT_X, null, TENANT_A);
        assertThat(issuedScope.customerAccountId()).isEqualTo(ACCOUNT_X);
        authorized.remove("alice");

        // Simulates a second request after a cached data hit (and a queued
        // task attempting to reuse an earlier scope). A fresh call MUST DENY.
        assertThatThrownBy(() -> gate.authorize(
                token, TENANT_A, ACCOUNT_X, null, TENANT_A))
                .isInstanceOf(AccessDeniedException.class);
        assertThat(checks).hasValue(2);
    }

    @Test
    void signedTenantHintAndCrossAccountResourceCannotExpandGrant() {
        var gate = new TenantScopeAuthorization((subject, tenant, account) ->
                "alice".equals(subject) && TENANT_A.equals(tenant)
                        && ACCOUNT_X.equals(account));
        var jwt = actor("alice"); // deliberately contains tenant B claim
        assertThat(gate.authorize(jwt, TENANT_A, ACCOUNT_X, null, TENANT_A)
                .tenantId()).isEqualTo(TENANT_A);
        assertThatThrownBy(() -> gate.authorize(jwt, TENANT_B, ACCOUNT_X, null, TENANT_B))
                .isInstanceOf(AccessDeniedException.class);
        assertThatThrownBy(() -> gate.authorize(jwt, TENANT_A, ACCOUNT_Y, null, TENANT_A))
                .isInstanceOf(AccessDeniedException.class);
        assertThatThrownBy(() -> gate.authorize(
                jwt, TENANT_A, ACCOUNT_X, TENANT_B.toString(), TENANT_A))
                .isInstanceOf(AccessDeniedException.class);
    }

    @Test
    void nonJwtIdentityAndUnavailableGrantSourceFailClosed() {
        var gate = new TenantScopeAuthorization((subject, tenant, account) -> true);
        var nonJwt = new TestingAuthenticationToken("alice", "test");
        nonJwt.setAuthenticated(true);
        assertThatThrownBy(() -> gate.authorize(
                nonJwt, TENANT_A, ACCOUNT_X, null, TENANT_A))
                .isInstanceOf(AccessDeniedException.class);

        var unavailable = new TenantScopeAuthorization((subject, tenant, account) -> {
            throw new IllegalStateException("grant store unavailable");
        });
        assertThatThrownBy(() -> unavailable.authorize(
                actor("alice"), TENANT_A, ACCOUNT_X, null, TENANT_A))
                .isInstanceOf(IllegalStateException.class);
        // The exception must never be converted to an allow decision.
    }
}
