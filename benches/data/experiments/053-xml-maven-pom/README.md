# Experiment: xml-maven-pom

**Format:** application/xml | **Size:** medium | **Edits:** 3

**Expected sections:** properties, dependencies, build, profiles

## Protocol cost (the only difference from base)

| Prompt | Chars | ~Tokens |
|---|---|---|
| Base system | 96 | 24 |
| AAP init system | 249 | 62 |
| AAP maintain system | 859 | 214 |
| **Protocol overhead** | | **~253 tokens** |

## Turns

| Turn | Edit |
|---|---|
| 0 | (creation) |
| 1 | Add spring-boot-starter-cache and caffeine dependencies for local caching sup... |
| 2 | Rewrite the profiles section to add a 'test' profile with H2 in-memory databa... |
| 3 | Add the jib-maven-plugin to the build section for containerizing the applicat... |
