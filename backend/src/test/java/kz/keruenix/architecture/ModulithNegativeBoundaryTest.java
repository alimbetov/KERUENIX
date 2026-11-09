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
        assertThatThrownBy(() -> ApplicationModules.of(FixtureRoot.class).verify())
                .isInstanceOf(RuntimeException.class)
                .hasMessageContaining("RepositoryInternal");
    }

    @Test
    void actualProductionModuleGraphRemainsValid() {
        ApplicationModules.of(KeruenixApplication.class).verify();
    }
}
