package kz.keruenix.platform.security;

import kz.keruenix.platform.errors.SecurityProblemHandler;
import jakarta.servlet.DispatcherType;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.config.annotation.web.configurers.AbstractHttpConfigurer;
import org.springframework.security.config.http.SessionCreationPolicy;
import org.springframework.security.web.SecurityFilterChain;

/**
 * Fail-closed bootstrap: no public business endpoint or working login is configured.
 * Replace denyAll with tenant-aware verified authorization when Tenancy/JWT is built.
 */
@Configuration
public class SecurityConfig {
    @Bean
    SecurityFilterChain apiSecurity(HttpSecurity http, SecurityProblemHandler errors) throws Exception {
        http
            .csrf(csrf -> csrf.ignoringRequestMatchers(
                request -> request.getDispatcherType() == DispatcherType.ERROR))
            .sessionManagement(s -> s.sessionCreationPolicy(SessionCreationPolicy.STATELESS))
            .formLogin(AbstractHttpConfigurer::disable)
            .httpBasic(AbstractHttpConfigurer::disable)
            .exceptionHandling(e -> e
                .authenticationEntryPoint(errors)
                .accessDeniedHandler(errors))
            .authorizeHttpRequests(a -> a
                .dispatcherTypeMatchers(DispatcherType.ERROR).permitAll()
                .anyRequest().denyAll());
        // CSRF deliberately remains enabled until the browser/API auth strategy is chosen.
        return http.build();
    }
}
