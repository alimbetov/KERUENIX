package kz.keruenix.platform.persistence;

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
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.test.context.ActiveProfiles;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

/**
 * S1 candidate: actual database invariants, not a business module and not legal approval.
 * Test-only tables are installed by the isolated CI migrator, never by the runtime app.
 * This suite must execute on a real PostgreSQL/PostGIS server under the app RLS role.
 */
@EnabledIfEnvironmentVariable(named = "KERUENIX_DB_URL", matches = "jdbc:postgresql:.*")
@SpringBootTest
@ActiveProfiles({"platform-db", "platform-db-migrate-test"})
class FoundationAtomicityGeographyContractTest {
    private static final UUID TENANT_A =
            UUID.fromString("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa");
    private static final UUID TENANT_B =
            UUID.fromString("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb");
    private static final String DIGEST = "a".repeat(64);

    @Autowired DataSource source;
    private PlatformTenantTransaction transactions;

    @BeforeEach
    void installSyntheticFixturesUsingSeparateMigratorPrincipal() throws Exception {
        try (Connection admin = DriverManager.getConnection(
                System.getenv("KERUENIX_DB_URL"),
                System.getenv("KERUENIX_DB_MIGRATOR_USER"),
                System.getenv("KERUENIX_DB_MIGRATOR_PASSWORD"));
             Statement statement = admin.createStatement()) {
            statement.execute("""
                    CREATE TABLE IF NOT EXISTS platform.qualification_aggregate (
                        tenant_id uuid NOT NULL,
                        aggregate_id uuid NOT NULL,
                        version integer NOT NULL CHECK (version > 0),
                        PRIMARY KEY (tenant_id, aggregate_id)
                    )
                    """);
            statement.execute("""
                    CREATE TABLE IF NOT EXISTS platform.qualification_geo (
                        tenant_id uuid NOT NULL,
                        location_id uuid NOT NULL,
                        position geography(Point,4326) NOT NULL,
                        PRIMARY KEY (tenant_id, location_id)
                    )
                    """);
            statement.execute("""
                    ALTER TABLE platform.qualification_aggregate ENABLE ROW LEVEL SECURITY;
                    ALTER TABLE platform.qualification_aggregate FORCE ROW LEVEL SECURITY;
                    DROP POLICY IF EXISTS q_aggregate_scope ON platform.qualification_aggregate;
                    CREATE POLICY q_aggregate_scope ON platform.qualification_aggregate
                      USING (tenant_id = platform.current_tenant_id())
                      WITH CHECK (tenant_id = platform.current_tenant_id());
                    ALTER TABLE platform.qualification_geo ENABLE ROW LEVEL SECURITY;
                    ALTER TABLE platform.qualification_geo FORCE ROW LEVEL SECURITY;
                    DROP POLICY IF EXISTS q_geo_scope ON platform.qualification_geo;
                    CREATE POLICY q_geo_scope ON platform.qualification_geo
                      USING (tenant_id = platform.current_tenant_id())
                      WITH CHECK (tenant_id = platform.current_tenant_id());
                    """);
            statement.execute("""
                    GRANT USAGE ON SCHEMA platform TO keruenix_app;
                    GRANT SELECT, INSERT ON platform.qualification_aggregate TO keruenix_app;
                    GRANT SELECT, INSERT ON platform.qualification_geo TO keruenix_app;
                    GRANT keruenix_app TO keruenix_ci_login;
                    """);
            // Existing platform tables are also needed by the command's audit/outbox.
            statement.execute("GRANT SELECT, INSERT ON platform.audit_fact TO keruenix_app");
            statement.execute("GRANT SELECT, INSERT ON platform.outbox_event TO keruenix_app");
        }
        transactions = new PlatformTenantTransaction(source);
    }

    /** FOUND-04: test aggregate + audit + outbox share exactly one transaction. */
    @Test
    void found04RollbackAndControlCommitHaveThreeMatchingRecords() {
        UUID aggregate = UUID.randomUUID();
        UUID audit = UUID.randomUUID();
        UUID event = UUID.randomUUID();
        assertThatThrownBy(() -> transactions.execute(TENANT_A, jdbc -> {
            insertTriplet(jdbc, aggregate, audit, event);
            throw new IllegalStateException("fault injected before commit");
        })).isInstanceOf(IllegalStateException.class)
                .hasMessageContaining("fault injected");

        // Independent post-rollback transaction: no phantom partial success.
        transactions.execute(TENANT_A, jdbc -> {
            assertTripletCount(jdbc, aggregate, audit, event, 0);
            return null;
        });

        // Control proves that the same commands are executable when committed.
        transactions.execute(TENANT_A, jdbc -> {
            insertTriplet(jdbc, aggregate, audit, event);
            return null;
        });
        transactions.execute(TENANT_A, jdbc -> {
            assertTripletCount(jdbc, aggregate, audit, event, 1);
            return null;
        });
        transactions.execute(TENANT_B, jdbc -> {
            assertTripletCount(jdbc, aggregate, audit, event, 0);
            return null;
        });
    }

    /** FOUND-12: geography is measured in meters and foreign tenant rows stay invisible. */
    @Test
    void found12MeterDistanceAndTenantRlsAreEnforced() {
        UUID location = UUID.randomUUID();
        transactions.execute(TENANT_A, jdbc -> {
            jdbc.update("""
                    INSERT INTO platform.qualification_geo
                      (tenant_id, location_id, position)
                    VALUES (?, ?, ST_SetSRID(ST_MakePoint(76.9,43.2),4326)::geography)
                    """, TENANT_A, location);
            assertThat(jdbc.queryForObject("""
                    SELECT count(*) FROM platform.qualification_geo
                    WHERE ST_DWithin(position,
                      ST_SetSRID(ST_MakePoint(76.9001,43.2),4326)::geography, 20)
                    """, Integer.class)).isEqualTo(1);
            assertThat(jdbc.queryForObject("""
                    SELECT count(*) FROM platform.qualification_geo
                    WHERE ST_DWithin(position,
                      ST_SetSRID(ST_MakePoint(77.0,43.2),4326)::geography, 1000)
                    """, Integer.class)).isZero();
            return null;
        });
        transactions.execute(TENANT_B, jdbc -> {
            assertThat(jdbc.queryForObject(
                    "SELECT count(*) FROM platform.qualification_geo WHERE location_id=?",
                    Integer.class, location)).isZero();
            return null;
        });
        // PostgreSQL/PostGIS geography input alone does not enforce the intended
        // application lon/lat validation policy: that remains an explicit RED target.
    }

    private static void insertTriplet(JdbcTemplate jdbc, UUID aggregate, UUID audit, UUID event) {
        jdbc.update("""
                INSERT INTO platform.qualification_aggregate (tenant_id,aggregate_id,version)
                VALUES (?, ?, 1)
                """, TENANT_A, aggregate);
        jdbc.update("""
                INSERT INTO platform.audit_fact
                  (tenant_id,audit_id,actor_ref,action_type,subject_ref)
                VALUES (?, ?,'ci:verified','Qualification',?)
                """, TENANT_A, audit, aggregate.toString());
        jdbc.update("""
                INSERT INTO platform.outbox_event
                  (tenant_id,event_id,event_type,aggregate_ref,payload_schema_version,
                   payload,payload_sha256)
                VALUES (?, ?,'Qualification',?,1,
                        jsonb_build_object('aggregateId', CAST(? AS text), 'version', 1),?)
                """, TENANT_A, event, "qualification:" + aggregate, aggregate, DIGEST);
    }

    private static void assertTripletCount(JdbcTemplate jdbc, UUID aggregate,
                                           UUID audit, UUID event, int expected) {
        assertThat(jdbc.queryForObject(
                "SELECT count(*) FROM platform.qualification_aggregate WHERE aggregate_id=?",
                Integer.class, aggregate)).isEqualTo(expected);
        assertThat(jdbc.queryForObject(
                "SELECT count(*) FROM platform.audit_fact WHERE audit_id=?",
                Integer.class, audit)).isEqualTo(expected);
        assertThat(jdbc.queryForObject(
                "SELECT count(*) FROM platform.outbox_event WHERE event_id=?",
                Integer.class, event)).isEqualTo(expected);
        if (expected == 1) {
            assertThat(jdbc.queryForObject(
                    "SELECT version FROM platform.qualification_aggregate WHERE aggregate_id=?",
                    Integer.class, aggregate)).isEqualTo(1);
            assertThat(jdbc.queryForObject(
                    "SELECT subject_ref FROM platform.audit_fact WHERE audit_id=?",
                    String.class, audit)).isEqualTo(aggregate.toString());
            assertThat(jdbc.queryForObject(
                    "SELECT aggregate_ref FROM platform.outbox_event WHERE event_id=?",
                    String.class, event)).isEqualTo("qualification:" + aggregate);
            assertThat(jdbc.queryForObject(
                    "SELECT payload->>'aggregateId' FROM platform.outbox_event WHERE event_id=?",
                    String.class, event)).isEqualTo(aggregate.toString());
            assertThat(jdbc.queryForObject(
                    "SELECT (payload->>'version')::integer FROM platform.outbox_event WHERE event_id=?",
                    Integer.class, event)).isEqualTo(1);
        }
    }
}
