package kz.keruenix.platform.persistence;

import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.Statement;

import liquibase.integration.spring.SpringLiquibase;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.condition.EnabledIfEnvironmentVariable;
import org.springframework.jdbc.datasource.DriverManagerDataSource;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

/**
 * FOUND-10 checksum drift: destructive mutation is confined to a DEDICATED
 * disposable CI database, never the shared integration database.
 */
@EnabledIfEnvironmentVariable(named = "KERUENIX_CHECKSUM_DB_URL", matches = "jdbc:postgresql:.*")
class LiquibaseChecksumDriftContractTest {
    @Test
    void alteredAppliedChecksumFailsValidationAndLeavesBusinessTablesUnchanged() throws Exception {
        String url = System.getenv("KERUENIX_CHECKSUM_DB_URL");
        String user = System.getenv("KERUENIX_DB_MIGRATOR_USER");
        String password = System.getenv("KERUENIX_DB_MIGRATOR_PASSWORD");
        String originalChecksum;
        long before;
        try (Connection connection = DriverManager.getConnection(url, user, password)) {
            try (Statement statement = connection.createStatement();
                 ResultSet result = statement.executeQuery("""
                       SELECT count(*) FROM platform.outbox_event
                       """)) {
                assertThat(result.next()).isTrue();
                before = result.getLong(1);
            }
            try (PreparedStatement select = connection.prepareStatement("""
                    SELECT md5sum FROM public.databasechangelog
                    WHERE id='platform-baseline-v1' AND author='keruenix'
                    """);
                 ResultSet result = select.executeQuery()) {
                assertThat(result.next()).isTrue();
                originalChecksum = result.getString(1);
                assertThat(originalChecksum).isNotBlank();
            }
            try (PreparedStatement update = connection.prepareStatement("""
                    UPDATE public.databasechangelog SET md5sum=?
                    WHERE id='platform-baseline-v1' AND author='keruenix'
                    """)) {
                update.setString(1, "8:" + "0".repeat(32));
                assertThat(update.executeUpdate()).isEqualTo(1);
            }
        }

        try {
            var migrator = new DriverManagerDataSource(url, user, password);
            SpringLiquibase liquibase = new SpringLiquibase();
            liquibase.setDataSource(migrator);
            liquibase.setChangeLog("classpath:db/changelog/db.changelog-master.yaml");
            assertThatThrownBy(liquibase::afterPropertiesSet)
                    .hasStackTraceContaining("checksum");
        } finally {
            try (Connection connection = DriverManager.getConnection(url, user, password);
                 PreparedStatement restore = connection.prepareStatement("""
                    UPDATE public.databasechangelog SET md5sum=?
                    WHERE id='platform-baseline-v1' AND author='keruenix'
                    """)) {
                restore.setString(1, originalChecksum);
                assertThat(restore.executeUpdate()).isEqualTo(1);
            }
        }
        try (Connection connection = DriverManager.getConnection(url, user, password);
             Statement statement = connection.createStatement();
             ResultSet result = statement.executeQuery(
                     "SELECT count(*) FROM platform.outbox_event")) {
            assertThat(result.next()).isTrue();
            assertThat(result.getLong(1)).isEqualTo(before);
        }
    }
}
