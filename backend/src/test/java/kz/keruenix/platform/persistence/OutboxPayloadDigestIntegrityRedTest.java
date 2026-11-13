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
 * Audit A-03. Expected behavioral RED against actual PostgreSQL-backed
 * production OutboxDelivery (no fake sender dispatch or mocked database).
 *
 * The schema accepts any lowercase 64-digit hex "payload_sha256", including a
 * digest with no relationship to the serialized event body. A sender must not
 * see a body whose digest is wrong. No hash canonicalization contract has yet
 * been approved: this is a deliberately limited mismatch-negative oracle.
 */
@EnabledIfEnvironmentVariable(named = "KERUENIX_A03_DIGEST_RED", matches = "true")
@EnabledIfEnvironmentVariable(named = "KERUENIX_DB_URL", matches = "jdbc:postgresql:.*")
@SpringBootTest
@ActiveProfiles({"platform-db", "platform-db-migrate-test"})
class OutboxPayloadDigestIntegrityRedTest {
    private final UUID tenant = UUID.randomUUID();

    @Autowired DataSource dataSource;
    PlatformTenantTransaction app;
    PlatformOutboxDelivery dispatcher;

    @BeforeEach
    void setup() throws Exception {
        try (Connection c = DriverManager.getConnection(System.getenv("KERUENIX_DB_URL"),
                System.getenv("KERUENIX_DB_MIGRATOR_USER"),
                System.getenv("KERUENIX_DB_MIGRATOR_PASSWORD"));
             Statement sql = c.createStatement()) {
            sql.execute(Files.readString(Path.of("db/admin/bootstrap_roles.sql")));
            sql.execute("""
                    DO $role$ BEGIN
                      IF NOT EXISTS (SELECT FROM pg_roles
                        WHERE rolname='keruenix_ci_dispatcher') THEN
                        CREATE ROLE keruenix_ci_dispatcher LOGIN PASSWORD 'ci-only-dispatcher-pass';
                      END IF;
                    END $role$
                    """);
            sql.execute("GRANT keruenix_dispatcher TO keruenix_ci_dispatcher");
            sql.execute("GRANT keruenix_app TO keruenix_ci_login");
        }
        app = new PlatformTenantTransaction(dataSource);
        var role = new DriverManagerDataSource(System.getenv("KERUENIX_DB_URL"),
                "keruenix_ci_dispatcher", "ci-only-dispatcher-pass");
        var worker = new PlatformTenantTransaction(role);
        dispatcher = new PlatformOutboxDelivery(new PlatformOutboxClaims(worker), worker);
    }

    @Test
    void senderMustNotReceivePayloadWithMismatchingDigest() {
        UUID event = UUID.randomUUID();
        app.execute(tenant, jdbc -> {
            jdbc.update("""
                    INSERT INTO platform.outbox_event (
                      tenant_id,event_id,event_type,aggregate_ref,
                      payload_schema_version,payload,payload_sha256
                    ) VALUES (?,?,'DigestProbe','audit:digest',1,
                      '{"body":"digest-mismatch"}'::jsonb,?)
                    """, tenant,event,"0".repeat(64));
            return null;
        });
        AtomicInteger sendCount = new AtomicInteger();
        dispatcher.dispatchNext(tenant,"digest-probe",60,
                envelope -> sendCount.incrementAndGet());
        assertThat(sendCount.get())
                .as("A03_OUTBOX_DIGEST_MISMATCH_REACHED_SENDER")
                .isZero();
    }
}
