package kz.keruenix.platform.persistence;

import javax.sql.DataSource;

import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.condition.EnabledIfEnvironmentVariable;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.test.context.ActiveProfiles;

import static org.assertj.core.api.Assertions.assertThat;

/**
 * This test runs as a separate Maven process AFTER the migration integration
 * job. CI supplies only the app credentials. No privileged Flyway password.
 */
@EnabledIfEnvironmentVariable(named="KERUENIX_DB_URL", matches="jdbc:postgresql:.*")
@SpringBootTest
@ActiveProfiles("platform-db")
class RuntimeDatabaseProfileTest {
    @Autowired DataSource dataSource;

    @Test
    void bootStartsWithoutMigrationPrivilegesOrMigrationCredentials() {
        assertThat(System.getenv("KERUENIX_DB_MIGRATOR_USER")).isNull();
        assertThat(System.getenv("KERUENIX_DB_MIGRATOR_PASSWORD")).isNull();
        JdbcTemplate jdbc = new JdbcTemplate(dataSource);
        assertThat(jdbc.queryForObject("SELECT current_user",String.class))
                .isEqualTo("keruenix_ci_login");
        assertThat(jdbc.queryForObject("""
                SELECT rolsuper OR rolbypassrls OR rolcreatedb OR rolcreaterole
                FROM pg_roles WHERE rolname = current_user
                """,Boolean.class)).isFalse();
        assertThat(jdbc.queryForObject(
                "SELECT count(*) FROM platform.outbox_event",Integer.class)).isZero();
    }
}
