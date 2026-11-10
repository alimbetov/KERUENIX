package kz.keruenix.platform.persistence;

import java.nio.file.Files;
import java.nio.file.Path;
import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.Statement;
import java.util.UUID;
import java.util.concurrent.atomic.AtomicInteger;

import javax.sql.DataSource;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.condition.EnabledIfEnvironmentVariable;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.jdbc.datasource.DriverManagerDataSource;
import org.springframework.test.context.ActiveProfiles;

import static org.assertj.core.api.Assertions.assertThat;

/**
 * Issue #8 — BASELINE PASS proving the boundary of the REAL generic transport.
 *
 * This is a transport behavior diagnostic, NOT CustomerAccount authorization.
 * The future Account business caller (not this generic transport) must enforce
 * its current account+operation grants before any protected external effect.
 * It is NOT a specification to put HTTP JWT auth inside PlatformOutboxDelivery:
 * the eventual approved caller/dispatcher policy must enforce authorization.
 *
 * The production generic transport has NO account grant input today.
 * Do not interpret this as a working CustomerAccount job implementation.
 */
@EnabledIfEnvironmentVariable(
        named = "KERUENIX_ISSUE8_TRANSPORT_BASELINE", matches = "true")
@EnabledIfEnvironmentVariable(
        named = "KERUENIX_DB_URL", matches = "jdbc:postgresql:.*")
@SpringBootTest
@ActiveProfiles({"platform-db", "platform-db-migrate-test"})
class Issue8CustomerOutboxAuthorizationRedTest {

    // A random tenant keeps this isolated from unrelated pending outbox rows.
    private final UUID tenant = UUID.randomUUID();
    private static final UUID ACCOUNT_X =
            UUID.fromString("11111111-1111-1111-1111-111111111111");
    private static final UUID ACCOUNT_Y =
            UUID.fromString("22222222-2222-2222-2222-222222222222");

    @Autowired DataSource dataSource;
    PlatformTenantTransaction appScope;
    PlatformOutboxDelivery delivery;

    @BeforeEach
    void prepareRealRestrictedRoles() throws Exception {
        try (Connection admin = DriverManager.getConnection(
                System.getenv("KERUENIX_DB_URL"),
                System.getenv("KERUENIX_DB_MIGRATOR_USER"),
                System.getenv("KERUENIX_DB_MIGRATOR_PASSWORD"));
             Statement ddl = admin.createStatement()) {
            ddl.execute(Files.readString(Path.of("db/admin/bootstrap_roles.sql")));
            ddl.execute("""
                    DO $roles$ BEGIN
                      IF NOT EXISTS (SELECT FROM pg_roles
                        WHERE rolname='keruenix_ci_dispatcher') THEN
                        CREATE ROLE keruenix_ci_dispatcher LOGIN
                          PASSWORD 'ci-only-dispatcher-pass';
                      END IF;
                    END $roles$
                    """);
            ddl.execute("GRANT keruenix_dispatcher TO keruenix_ci_dispatcher");
            ddl.execute("GRANT keruenix_app TO keruenix_ci_login");
        }
        appScope = new PlatformTenantTransaction(dataSource);
        var dispatcher = new DriverManagerDataSource(System.getenv("KERUENIX_DB_URL"),
                "keruenix_ci_dispatcher", "ci-only-dispatcher-pass");
        var scoped = new PlatformTenantTransaction(dispatcher);
        delivery = new PlatformOutboxDelivery(new PlatformOutboxClaims(scoped), scoped);
    }

    @Test
    void genericTransportDeliversAnEventWithoutInspectingCustomerAccountGrants() {
        // A server-side grant for ACCOUNT_X MUST NOT grant access to ACCOUNT_Y.
        // No grant source is connected to the current generic dispatch path.
        // This seeded account-specific intent deliberately lacks authorization.
        UUID event = UUID.randomUUID();
        appScope.execute(tenant, jdbc -> {
            jdbc.update("""
                    INSERT INTO platform.outbox_event
                      (tenant_id,event_id,event_type,aggregate_ref,
                       payload_schema_version,payload,payload_sha256)
                    VALUES (?,?,'CustomerAccountExport','account:restricted',1,
                      jsonb_build_object('customerAccountId',CAST(? AS text),
                                         'operation','EXPORT'),?)
                    """, tenant, event, ACCOUNT_Y, "e".repeat(64));
            return null;
        });

        var sent = new AtomicInteger();
        boolean dispatched = delivery.dispatchNext(tenant, "issue8-dispatcher",
                60, envelope -> {
                    assertThat(envelope.eventId()).isEqualTo(event);
                    sent.incrementAndGet();
                });

        // Expected PASS for a generic transport; NOT an authorization oracle.
        // A future authorized caller must prevent unverified account operation
        // events from reaching this generic dispatcher at all.
        assertThat(sent.get()).as("generic Outbox emits a claimed event").isEqualTo(1);
        assertThat(dispatched).isTrue();
    }
}
