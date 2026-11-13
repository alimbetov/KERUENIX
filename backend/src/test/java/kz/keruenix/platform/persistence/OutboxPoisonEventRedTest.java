package kz.keruenix.platform.persistence;

import java.nio.file.Files;
import java.nio.file.Path;
import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.Statement;
import java.util.UUID;

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
 * A-04 S1: expected behavior RED against real PostgreSQL queue and real
 * PlatformOutboxClaims. MAX_ATTEMPTS=3 is a proposed R0 operational policy,
 * NOT a production setting. The test must remain isolated from normal verify.
 */
@EnabledIfEnvironmentVariable(named="KERUENIX_A04_RETRY_RED", matches="true")
@EnabledIfEnvironmentVariable(named="KERUENIX_DB_URL", matches="jdbc:postgresql:.*")
@SpringBootTest
@ActiveProfiles({"platform-db", "platform-db-migrate-test"})
class OutboxPoisonEventRedTest {
    private final UUID tenant = UUID.randomUUID();
    @Autowired DataSource dataSource;
    PlatformTenantTransaction app;
    PlatformOutboxClaims claims;

    @BeforeEach
    void setup() throws Exception {
        try (Connection admin=DriverManager.getConnection(System.getenv("KERUENIX_DB_URL"),
                System.getenv("KERUENIX_DB_MIGRATOR_USER"),
                System.getenv("KERUENIX_DB_MIGRATOR_PASSWORD"));
                Statement sql=admin.createStatement()) {
            sql.execute(Files.readString(Path.of("db/admin/bootstrap_roles.sql")));
            sql.execute("""
                    DO $role$ BEGIN
                      IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname='keruenix_ci_dispatcher')
                      THEN CREATE ROLE keruenix_ci_dispatcher LOGIN
                        PASSWORD 'ci-only-dispatcher-pass'; END IF;
                    END $role$
                    """);
            sql.execute("GRANT keruenix_dispatcher TO keruenix_ci_dispatcher");
            sql.execute("GRANT keruenix_app TO keruenix_ci_login");
        }
        app=new PlatformTenantTransaction(dataSource);
        var worker = new DriverManagerDataSource(System.getenv("KERUENIX_DB_URL"),
                "keruenix_ci_dispatcher","ci-only-dispatcher-pass");
        claims=new PlatformOutboxClaims(new PlatformTenantTransaction(worker));
    }

    @Test
    void poisonEventTransitionsToDeadLetterAfterThreeFailedClaims() {
        UUID event = UUID.randomUUID();
        app.execute(tenant,jdbc -> {
            jdbc.update("""
                    INSERT INTO platform.outbox_event(
                        tenant_id,event_id,event_type,aggregate_ref,
                        payload_schema_version,payload,payload_sha256)
                    VALUES (?,?,'PoisonProbe','probe:dead-letter',1,'{}'::jsonb,?)
                    """,tenant,event,"a".repeat(64));
            return null;
        });
        for(int attempt=1;attempt<=3;attempt++) {
            var claim=claims.claimNext(tenant,"poison-worker-"+attempt,30).orElseThrow();
            assertThat(claim.eventId()).isEqualTo(event);
            assertThat(claim.attemptCount()).isEqualTo(attempt);
            assertThat(claims.scheduleRetry(tenant,claim,0)).isTrue();
        }
        String state=app.execute(tenant,jdbc -> jdbc.queryForObject(
                "SELECT delivery_state FROM platform.outbox_event WHERE event_id=?",
                String.class,event));
        assertThat(state).as("A04_POISON_EVENT_REMAINS_RETRYABLE_AFTER_MAX_ATTEMPTS")
                .isEqualTo("DEAD_LETTER");
        assertThat(claims.claimNext(tenant,"fourth-worker",30)).isEmpty();
    }
}
