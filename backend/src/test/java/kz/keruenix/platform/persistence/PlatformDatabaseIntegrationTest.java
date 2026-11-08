package kz.keruenix.platform.persistence;

import java.nio.file.Files;
import java.nio.file.Path;
import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.Statement;
import java.util.UUID;

import javax.sql.DataSource;

import java.sql.ResultSet;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.condition.EnabledIfEnvironmentVariable;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.dao.DataAccessException;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.test.context.ActiveProfiles;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

/**
 * Real PostgreSQL/PostGIS integration test; cannot pass on an embedded database.
 * Enabled only in the dedicated GitHub Actions PostgreSQL foundation job.
 * It does not test actual JWT authority or external broker delivery; lease fencing has a separate DB test.
 */
@EnabledIfEnvironmentVariable(named = "KERUENIX_DB_URL", matches = "jdbc:postgresql:.*")
@SpringBootTest
@ActiveProfiles({"platform-db", "platform-db-migrate-test"})
class PlatformDatabaseIntegrationTest {
    private static final UUID TENANT_A =
            UUID.fromString("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa");
    private static final UUID TENANT_B =
            UUID.fromString("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb");
    private static final UUID SHARED_EVENT =
            UUID.fromString("10000000-0000-0000-0000-000000000001");
    private static final UUID SHARED_AUDIT =
            UUID.fromString("20000000-0000-0000-0000-000000000001");
    private static final String DIGEST_A = "a".repeat(64);
    private static final String DIGEST_B = "b".repeat(64);

    @Autowired DataSource dataSource;
    @Autowired JdbcTemplate jdbc;
    PlatformTenantTransaction scope;

    @BeforeEach
    void prepareRuntimeGrantsAfterLiquibaseStartup() throws Exception {
        // The privileged DDL credential is never supplied to the business
        // DataSource; it is used only for migration/admin tasks in isolated CI.
        try (Connection admin = DriverManager.getConnection(
                System.getenv("KERUENIX_DB_URL"),
                System.getenv("KERUENIX_DB_MIGRATOR_USER"),
                System.getenv("KERUENIX_DB_MIGRATOR_PASSWORD"));
             Statement ddl = admin.createStatement()) {
            ddl.execute(Files.readString(Path.of("db/admin/bootstrap_roles.sql")));
            ddl.execute("GRANT keruenix_app TO keruenix_ci_login");
        }
        scope = new PlatformTenantTransaction(dataSource);
    }

    @Test
    void springBootLiquibaseMigratesWithSeparateAdminAndRuntimeAccounts() throws Exception {
        try (Connection admin = DriverManager.getConnection(
                System.getenv("KERUENIX_DB_URL"),
                System.getenv("KERUENIX_DB_MIGRATOR_USER"),
                System.getenv("KERUENIX_DB_MIGRATOR_PASSWORD"));
             Statement statement = admin.createStatement();
             ResultSet rows = statement.executeQuery(
                     "SELECT id, author FROM public.databasechangelog ORDER BY orderexecuted")) {
            assertThat(rows.next()).isTrue();
            assertThat(rows.getString("id")).isEqualTo("platform-baseline-v1");
            assertThat(rows.getString("author")).isEqualTo("keruenix");
            assertThat(rows.next()).isTrue();
            assertThat(rows.getString("id")).isEqualTo("outbox-fencing-v2");
            assertThat(rows.next()).isFalse();
        }
        assertThat(jdbc.queryForObject("SELECT current_user", String.class))
                .isEqualTo("keruenix_ci_login");
        assertThat(jdbc.queryForObject("""
                SELECT rolsuper OR rolbypassrls OR rolcreatedb OR rolcreaterole
                FROM pg_roles WHERE rolname = current_user
                """, Boolean.class)).isFalse();
        assertThat(jdbc.queryForObject("""
                SELECT bool_and(relrowsecurity AND relforcerowsecurity)
                FROM pg_class
                WHERE oid IN ('platform.outbox_event'::regclass,
                              'platform.audit_fact'::regclass,
                              'platform.inbox_receipt'::regclass)
                """, Boolean.class)).isTrue();
        assertThatThrownBy(() -> jdbc.execute(
                "CREATE TABLE platform.unauthorized_ddl(id uuid)"))
                .isInstanceOf(DataAccessException.class);
    }

    @Test
    void noContextAndTenantSwitchingInPooledDatasourceCannotLeakRows() {
        assertThat(jdbc.queryForObject("""
                SELECT NULLIF(current_setting('keruenix.tenant_id', true),'')
                """, String.class)).isNull();
        assertThat(jdbc.queryForObject(
                "SELECT count(*) FROM platform.outbox_event", Integer.class)).isZero();

        scope.execute(TENANT_A, sql -> {
            insertOutbox(sql, TENANT_A, SHARED_EVENT, DIGEST_A);
            insertAudit(sql, TENANT_A, SHARED_AUDIT);
            assertThat(count(sql, "platform.outbox_event")).isEqualTo(1);
            return null;
        });
        assertThat(jdbc.queryForObject(
                "SELECT count(*) FROM platform.outbox_event", Integer.class)).isZero();

        scope.execute(TENANT_B, sql -> {
            assertThat(count(sql, "platform.outbox_event")).isZero();
            assertThat(count(sql, "platform.audit_fact")).isZero();
            // Tenant-first compound keys: no cross-tenant uniqueness oracle.
            insertOutbox(sql, TENANT_B, SHARED_EVENT, DIGEST_B);
            insertAudit(sql, TENANT_B, SHARED_AUDIT);
            assertThat(count(sql, "platform.outbox_event")).isEqualTo(1);
            return null;
        });
        scope.execute(TENANT_A, sql -> {
            assertThat(count(sql, "platform.outbox_event")).isEqualTo(1);
            assertThat(count(sql, "platform.audit_fact")).isEqualTo(1);
            return null;
        });
    }

    @Test
    void aggregateFactsAndInboxRollbackAsOneTransaction() {
        UUID e = UUID.randomUUID();
        UUID a = UUID.randomUUID();
        UUID received = UUID.randomUUID();
        assertThatThrownBy(() -> scope.execute(TENANT_A, sql -> {
            insertOutbox(sql, TENANT_A, e, DIGEST_A);
            insertAudit(sql, TENANT_A, a);
            new PlatformInbox().accept(sql, TENANT_A, "ci-rollback", received, DIGEST_A);
            throw new IllegalStateException("simulated pre-commit crash");
        })).isInstanceOf(IllegalStateException.class);

        scope.execute(TENANT_A, sql -> {
            assertThat(sql.queryForObject(
                    "SELECT count(*) FROM platform.outbox_event WHERE event_id=?",
                    Integer.class, e)).isZero();
            assertThat(sql.queryForObject(
                    "SELECT count(*) FROM platform.audit_fact WHERE audit_id=?",
                    Integer.class, a)).isZero();
            assertThat(sql.queryForObject(
                    "SELECT count(*) FROM platform.inbox_receipt WHERE event_id=?",
                    Integer.class, received)).isZero();
            return null;
        });
    }

    @Test
    void inboxReplayWithChangedDigestIsRejected() {
        UUID e = UUID.randomUUID();
        PlatformInbox inbox = new PlatformInbox();
        PlatformInbox.Result created = scope.execute(TENANT_A,
                sql -> inbox.accept(sql, TENANT_A, "ci-consumer", e, DIGEST_A));
        assertThat(created).isEqualTo(PlatformInbox.Result.NEW);
        PlatformInbox.Result replayed = scope.execute(TENANT_A,
                sql -> inbox.accept(sql, TENANT_A, "ci-consumer", e, DIGEST_A));
        assertThat(replayed).isEqualTo(PlatformInbox.Result.REPLAY_IDENTICAL);
        assertThatThrownBy(() -> scope.execute(TENANT_A,
                sql -> inbox.accept(sql,TENANT_A,"ci-consumer",e,DIGEST_B)))
                .isInstanceOf(IllegalStateException.class)
                .hasMessageContaining("different digest");
    }

    @Test
    void springJdbcNeverRunsUnscopedGeographyWrites() {
        // PostGIS uses geography meters; this is a capability smoke, not an API.
        assertThat(jdbc.queryForObject("""
                SELECT ST_DWithin(
                    ST_SetSRID(ST_MakePoint(76.9,43.2),4326)::geography,
                    ST_SetSRID(ST_MakePoint(77.0,43.2),4326)::geography, 1000)
                """, Boolean.class)).isFalse();
        assertThat(jdbc.queryForObject("""
                SELECT ST_DWithin(
                    ST_SetSRID(ST_MakePoint(76.9,43.2),4326)::geography,
                    ST_SetSRID(ST_MakePoint(77.0,43.2),4326)::geography, 15000)
                """, Boolean.class)).isTrue();
    }

    private static int count(JdbcTemplate sql, String trustedTableName) {
        return sql.queryForObject("SELECT count(*) FROM " + trustedTableName, Integer.class);
    }

    private static void insertOutbox(JdbcTemplate sql, UUID tenant, UUID event, String hash) {
        sql.update("""
                INSERT INTO platform.outbox_event(
                   tenant_id,event_id,event_type,aggregate_ref,payload_schema_version,
                   payload,payload_sha256)
                VALUES (?,?,'FoundationJdbc','test:probe',1,'{}'::jsonb,?)
                """, tenant, event, hash);
    }

    private static void insertAudit(JdbcTemplate sql, UUID tenant, UUID audit) {
        sql.update("""
                INSERT INTO platform.audit_fact(
                    tenant_id,audit_id,actor_ref,action_type,subject_ref)
                VALUES (?,?,'ci:verified','FoundationJdbc','test:probe')
                """, tenant, audit);
    }
}
