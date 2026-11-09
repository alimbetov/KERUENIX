package kz.keruenix.platform.persistence;

import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.ResultSet;
import java.sql.Statement;

import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.condition.EnabledIfEnvironmentVariable;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.test.context.ActiveProfiles;

import static org.assertj.core.api.Assertions.assertThat;

/** Verifies Liquibase applies only pending changeSets across JVM restarts. */
@EnabledIfEnvironmentVariable(named = "KERUENIX_DB_URL", matches = "jdbc:postgresql:.*")
@SpringBootTest
@ActiveProfiles({"platform-db", "platform-db-migrate-test"})
class LiquibaseMigrationStateTest {
    @Test
    void appliedChangeSetsMatchExpectedVersionWithoutReexecution() throws Exception {
        int expected = Integer.parseInt(System.getenv("KERUENIX_EXPECTED_CHANGESETS"));
        try (Connection connection = DriverManager.getConnection(
                    System.getenv("KERUENIX_DB_URL"),
                    System.getenv("KERUENIX_DB_MIGRATOR_USER"),
                    System.getenv("KERUENIX_DB_MIGRATOR_PASSWORD"));
             Statement statement = connection.createStatement();
             ResultSet rs = statement.executeQuery("""
                    SELECT id, author FROM public.databasechangelog
                    ORDER BY orderexecuted
                    """)) {
            assertThat(rs.next()).isTrue();
            assertThat(rs.getString("id")).isEqualTo("platform-baseline-v1");
            assertThat(rs.getString("author")).isEqualTo("keruenix");
            if (expected == 2) {
                assertThat(rs.next()).isTrue();
                assertThat(rs.getString("id")).isEqualTo("outbox-fencing-v2");
            }
            assertThat(rs.next()).isFalse();
        }
    }
}
