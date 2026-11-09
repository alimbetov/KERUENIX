package kz.keruenix.architecture;

import kz.keruenix.KeruenixApplication;
import kz.keruenix.architecture.fixture.FixtureRoot;
import org.junit.jupiter.api.Test;
import org.springframework.modulith.core.ApplicationModules;

import static org.assertj.core.api.Assertions.assertThatThrownBy;

/** FOUND-09: a compilable forbidden import must be rejected by Modulith verification. */
class ModulithNegativeBoundaryTest {
    @Test
    void separateFixtureDetectsForbiddenInternalRepositoryDependency() {
        // The fixture lives under target/test-classes. Modulith's default
        // importer excludes test classes, so explicitly include this isolated
        // synthetic test root; the production verification stays unchanged.
        assertThatThrownBy(() -> ApplicationModules.of(FixtureRoot.class, location -> true).verify())
                .isInstanceOf(RuntimeException.class)
                .hasMessageContaining("RepositoryInternal");
    }

    @Test
    void actualProductionModuleGraphRemainsValid() {
        ApplicationModules.of(KeruenixApplication.class).verify();
    }
}
