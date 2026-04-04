Create a Maven pom.xml for a Spring Boot 3 web application.

Include:
- Parent: spring-boot-starter-parent
- Properties: Java 21, versions for dependencies
- Dependencies: spring-boot-starter-web, spring-boot-starter-data-jpa, spring-boot-starter-security, spring-boot-starter-validation, postgresql, flyway, lombok, mapstruct, springdoc-openapi
- Test dependencies: spring-boot-starter-test, testcontainers
- Build plugins: spring-boot-maven-plugin, mapstruct-processor, jacoco
- Profiles: dev, staging, production with different properties
