package kz.keruenix.platform.persistence;

import java.nio.file.Files;
import java.nio.file.Path;
import java.security.KeyPair;
import java.security.KeyPairGenerator;
import java.security.interfaces.RSAPrivateKey;
import java.security.interfaces.RSAPublicKey;
import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.Statement;
import java.time.Instant;
import java.util.Date;
import java.util.Map;
import java.util.UUID;

import javax.sql.DataSource;

import com.nimbusds.jose.JWSAlgorithm;
import com.nimbusds.jose.JWSHeader;
import com.nimbusds.jose.crypto.RSASSASigner;
import com.nimbusds.jwt.JWTClaimsSet;
import com.nimbusds.jwt.SignedJWT;
import kz.keruenix.platform.errors.SecurityProblemHandler;
import kz.keruenix.platform.security.TenantScopeAuthorization;
import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.condition.EnabledIfEnvironmentVariable;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.context.TestConfiguration;
import org.springframework.boot.webmvc.test.autoconfigure.AutoConfigureMockMvc;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Import;
import org.springframework.core.annotation.Order;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.security.config.Customizer;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.config.annotation.web.configurers.AbstractHttpConfigurer;
import org.springframework.security.config.http.SessionCreationPolicy;
import org.springframework.security.core.Authentication;
import org.springframework.security.oauth2.core.OAuth2Error;
import org.springframework.security.oauth2.core.OAuth2TokenValidator;
import org.springframework.security.oauth2.core.OAuth2TokenValidatorResult;
import org.springframework.security.oauth2.core.DelegatingOAuth2TokenValidator;
import org.springframework.security.oauth2.jwt.Jwt;
import org.springframework.security.oauth2.jwt.JwtDecoder;
import org.springframework.security.oauth2.jwt.JwtValidators;
import org.springframework.security.oauth2.jwt.NimbusJwtDecoder;
import org.springframework.security.web.SecurityFilterChain;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestHeader;
import org.springframework.web.bind.annotation.RestController;

import static org.assertj.core.api.Assertions.assertThat;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

/**
 * FOUND-03/08/11: real RSA-signed HTTP JWT -> server grant -> PostgreSQL RLS.
 * Test-only route and grant adapter. Production remains DENY ALL.
 */
@EnabledIfEnvironmentVariable(named = "KERUENIX_DB_URL", matches = "jdbc:postgresql:.*")
@SpringBootTest
@AutoConfigureMockMvc
@Import(TrustedTenantHttpIntegrationTest.QualificationConfig.class)
@org.springframework.test.context.ActiveProfiles({"platform-db", "platform-db-migrate-test"})
class TrustedTenantHttpIntegrationTest {
    static final String ISSUER = "https://issuer.keruenix.invalid/qualification";
    static final String AUDIENCE = "keruenix-api";
    static final UUID TENANT_A = UUID.fromString("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa");
    static final UUID TENANT_B = UUID.fromString("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb");
    static final UUID ACCOUNT_X = UUID.fromString("11111111-1111-1111-1111-111111111111");
    static final UUID ACCOUNT_Y = UUID.fromString("22222222-2222-2222-2222-222222222222");
    static KeyPair rsaKeys;

    @Autowired MockMvc mvc;
    @Autowired DataSource dataSource;

    @BeforeAll
    static void generateEphemeralSigningKey() throws Exception {
        var generator = KeyPairGenerator.getInstance("RSA");
        generator.initialize(2048);
        rsaKeys = generator.generateKeyPair();
    }

    @BeforeEach
    void allowRestrictedRuntimeRoleToWriteTestOnlyAudit() throws Exception {
        try (Connection admin = DriverManager.getConnection(
                System.getenv("KERUENIX_DB_URL"),
                System.getenv("KERUENIX_DB_MIGRATOR_USER"),
                System.getenv("KERUENIX_DB_MIGRATOR_PASSWORD"));
             Statement ddl = admin.createStatement()) {
            ddl.execute(Files.readString(Path.of("db/admin/bootstrap_roles.sql")));
            ddl.execute("GRANT keruenix_app TO keruenix_ci_login");
        }
    }

    private static String sign(String subject, String issuer, String audience,
                               Instant expiresAt, RSAPrivateKey key) throws Exception {
        var claims = new JWTClaimsSet.Builder()
                .issuer(issuer).subject(subject).audience(audience)
                .issueTime(new Date()).expirationTime(Date.from(expiresAt))
                // This claim is intentionally untrusted as a membership grant.
                .claim("tenant_id", TENANT_B.toString())
                .build();
        var signed = new SignedJWT(new JWSHeader(JWSAlgorithm.RS256), claims);
        signed.sign(new RSASSASigner(key));
        return signed.serialize();
    }

    private static String valid(String subject) throws Exception {
        return sign(subject, ISSUER, AUDIENCE, Instant.now().plusSeconds(300),
                (RSAPrivateKey) rsaKeys.getPrivate());
    }

    private static String uri(UUID tenant, UUID account) {
        return "/__qualification/tenant/" + tenant + "/account/" + account + "/probe";
    }

    private static String payload(UUID event, UUID tenant) {
        return "{\"eventId\":\"" + event + "\",\"tenantId\":\"" + tenant + "\"}";
    }

    private void assertAuditAbsent(UUID tenant, UUID event) {
        var scope = new PlatformTenantTransaction(dataSource);
        int matches = scope.execute(tenant, jdbc ->
                jdbc.queryForObject("SELECT count(*) FROM platform.audit_fact WHERE audit_id=?",
                        Integer.class, event));
        assertThat(matches).isZero();
    }

    @Test
    void signedJwtAndServerGrantedCustomerAccountCanWriteUnderTenantA() throws Exception {
        UUID event = UUID.randomUUID();
        mvc.perform(post(uri(TENANT_A, ACCOUNT_X))
                .header("Authorization", "Bearer " + valid("alice"))
                .header("X-Tenant-ID", TENANT_A)
                .contentType(MediaType.APPLICATION_JSON)
                .content(payload(event, TENANT_A)))
                .andExpect(status().isAccepted());

        var scope = new PlatformTenantTransaction(dataSource);
        assertThat(scope.execute(TENANT_A, jdbc -> jdbc.queryForObject(
                "SELECT count(*) FROM platform.audit_fact WHERE audit_id=?",
                Integer.class, event))).isEqualTo(1);
        assertAuditAbsent(TENANT_B, event);
    }

    @Test
    void signedJwtCannotSelectUnrelatedAccountInSameTenant() throws Exception {
        UUID event = UUID.randomUUID();
        mvc.perform(post(uri(TENANT_A, ACCOUNT_Y))
                .header("Authorization", "Bearer " + valid("alice"))
                .contentType(MediaType.APPLICATION_JSON)
                .content(payload(event, TENANT_A)))
                .andExpect(status().isForbidden())
                .andExpect(jsonPath("$.code").value("KX-AUTH-403-001"));
        assertAuditAbsent(TENANT_A, event);
    }

    @Test
    void bodyOrHeaderCannotOverrideTrustedTenant() throws Exception {
        UUID bodyEvent = UUID.randomUUID(), headerEvent = UUID.randomUUID();
        mvc.perform(post(uri(TENANT_A, ACCOUNT_X))
                .header("Authorization", "Bearer " + valid("alice"))
                .contentType(MediaType.APPLICATION_JSON)
                .content(payload(bodyEvent, TENANT_B)))
                .andExpect(status().isForbidden());
        mvc.perform(post(uri(TENANT_A, ACCOUNT_X))
                .header("Authorization", "Bearer " + valid("alice"))
                .header("X-Tenant-ID", TENANT_B)
                .contentType(MediaType.APPLICATION_JSON)
                .content(payload(headerEvent, TENANT_A)))
                .andExpect(status().isForbidden());
        assertAuditAbsent(TENANT_A, bodyEvent);
        assertAuditAbsent(TENANT_A, headerEvent);
        assertAuditAbsent(TENANT_B, bodyEvent);
    }

    @Test
    void signedTenantClaimAloneCannotGrantTenantBAccess() throws Exception {
        UUID event = UUID.randomUUID();
        mvc.perform(post(uri(TENANT_B, ACCOUNT_X))
                .header("Authorization", "Bearer " + valid("alice"))
                .contentType(MediaType.APPLICATION_JSON)
                .content(payload(event, TENANT_B)))
                .andExpect(status().isForbidden());
        assertAuditAbsent(TENANT_B, event);
    }

    @Test
    void forgedSignatureAndInvalidIssuerAndAudienceAreUnauthorized() throws Exception {
        var wrong = KeyPairGenerator.getInstance("RSA");
        wrong.initialize(2048);
        RSAPrivateKey attacker = (RSAPrivateKey) wrong.generateKeyPair().getPrivate();
        for (String jwt : new String[]{
                sign("alice", ISSUER, AUDIENCE, Instant.now().plusSeconds(300), attacker),
                sign("alice", "https://wrong.example", AUDIENCE,
                        Instant.now().plusSeconds(300), (RSAPrivateKey) rsaKeys.getPrivate()),
                sign("alice", ISSUER, "wrong-audience",
                        Instant.now().plusSeconds(300), (RSAPrivateKey) rsaKeys.getPrivate())
        }) {
            UUID event = UUID.randomUUID();
            mvc.perform(post(uri(TENANT_A, ACCOUNT_X))
                    .header("Authorization", "Bearer " + jwt)
                    .contentType(MediaType.APPLICATION_JSON)
                    .content(payload(event, TENANT_A)))
                    .andExpect(status().isUnauthorized());
            assertAuditAbsent(TENANT_A, event);
        }
    }

    @Test
    void expiredOrMissingJwtCannotReachDatabase() throws Exception {
        UUID expired = UUID.randomUUID(), missing = UUID.randomUUID();
        mvc.perform(post(uri(TENANT_A, ACCOUNT_X))
                .header("Authorization", "Bearer " + sign(
                        "alice", ISSUER, AUDIENCE, Instant.now().minusSeconds(3600),
                        (RSAPrivateKey) rsaKeys.getPrivate()))
                .contentType(MediaType.APPLICATION_JSON)
                .content(payload(expired, TENANT_A)))
                .andExpect(status().isUnauthorized());
        mvc.perform(post(uri(TENANT_A, ACCOUNT_X))
                .contentType(MediaType.APPLICATION_JSON)
                .content(payload(missing, TENANT_A)))
                .andExpect(status().isUnauthorized());
        assertAuditAbsent(TENANT_A, expired);
        assertAuditAbsent(TENANT_A, missing);
    }

    @TestConfiguration(proxyBeanMethods = false)
    static class QualificationConfig {
        @Bean
        TenantScopeAuthorization qualifier() {
            // Synthetic server-side grant fixture; NOT a production grant database.
            return new TenantScopeAuthorization((subject, tenant, account) ->
                    tenant.equals(TENANT_A) &&
                            (("alice".equals(subject) && ACCOUNT_X.equals(account))
                              || ("bob".equals(subject) && ACCOUNT_Y.equals(account))));
        }

        @Bean
        JwtDecoder qualificationDecoder() {
            var decoder = NimbusJwtDecoder.withPublicKey(
                    (RSAPublicKey) rsaKeys.getPublic()).build();
            OAuth2TokenValidator<Jwt> audience = jwt ->
                    jwt.getAudience().contains(AUDIENCE)
                            ? OAuth2TokenValidatorResult.success()
                            : OAuth2TokenValidatorResult.failure(
                                    new OAuth2Error("invalid_token", "Invalid audience", null));
            decoder.setJwtValidator(new DelegatingOAuth2TokenValidator<>(
                    JwtValidators.createDefaultWithIssuer(ISSUER), audience));
            return decoder;
        }

        @Bean
        @Order(1)
        SecurityFilterChain qualificationSecurity(HttpSecurity http,
                SecurityProblemHandler errors) throws Exception {
            http.securityMatcher("/__qualification/**")
                // Test-only endpoint; production SecurityConfig remains denyAll.
                .csrf(AbstractHttpConfigurer::disable)
                .sessionManagement(s -> s.sessionCreationPolicy(SessionCreationPolicy.STATELESS))
                .authorizeHttpRequests(a -> a.anyRequest().authenticated())
                .exceptionHandling(e -> e
                        .authenticationEntryPoint(errors).accessDeniedHandler(errors))
                .oauth2ResourceServer(o -> o
                        .authenticationEntryPoint(errors)
                        .accessDeniedHandler(errors)
                        .jwt(Customizer.withDefaults()));
            return http.build();
        }

        @Bean
        QualificationProbeController testProbeController(DataSource dataSource,
                TenantScopeAuthorization grants) {
            return new QualificationProbeController(dataSource, grants);
        }
    }

    @RestController
    static class QualificationProbeController {
        private final PlatformTenantTransaction transactions;
        private final TenantScopeAuthorization authorization;

        QualificationProbeController(DataSource source, TenantScopeAuthorization grants) {
            this.transactions = new PlatformTenantTransaction(source);
            this.authorization = grants;
        }

        record ProbeCommand(UUID eventId, UUID tenantId) {}

        @PostMapping("/__qualification/tenant/{tenant}/account/{account}/probe")
        ResponseEntity<Map<String, String>> write(
                Authentication authentication,
                @PathVariable UUID tenant, @PathVariable UUID account,
                @RequestHeader(value = "X-Tenant-ID", required = false) String header,
                @RequestBody ProbeCommand command) {
            var scope = authorization.authorize(
                    authentication, tenant, account, header, command.tenantId());
            transactions.execute(scope.tenantId(), jdbc -> {
                jdbc.update("""
                        INSERT INTO platform.audit_fact
                        (tenant_id,audit_id,actor_ref,action_type,subject_ref)
                        VALUES (?, ?, ?, 'AuthQualification', ?)
                        """, scope.tenantId(), command.eventId(), scope.subject(),
                        scope.customerAccountId().toString());
                return null;
            });
            return ResponseEntity.accepted().body(Map.of("status", "ACCEPTED"));
        }
    }
}
