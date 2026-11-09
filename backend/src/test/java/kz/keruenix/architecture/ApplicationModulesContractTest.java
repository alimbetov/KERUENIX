package kz.keruenix.architecture;

import kz.keruenix.KeruenixApplication;
import org.junit.jupiter.api.Test;
import org.springframework.modulith.core.ApplicationModules;

/**
 * Real Spring Modulith module graph verification.
 * Current implementation has only infrastructure packages; all 17 planned
 * business modules are specifications, not discovered Java modules yet.
 */
class ApplicationModulesContractTest {
    @Test
    void currentJavaModuleGraphHasNoForbiddenDependenciesOrCycles() {
        ApplicationModules.of(KeruenixApplication.class).verify();
    }
}
