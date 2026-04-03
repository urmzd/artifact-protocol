Create a Spring Boot REST controller for product management.

Include:
- ProductController with @RestController: CRUD endpoints, search, pagination, sorting
- ProductService: business logic, validation, caching with @Cacheable
- ProductRepository: JPA repository with custom query methods
- DTOs: ProductRequest, ProductResponse, ProductSearchCriteria, PagedResponse
- Exception handling with @ControllerAdvice
- Proper annotations, validation, and Javadoc

Use section IDs: imports, controller, service, repository

Use AAP section markers to delineate each major code block.
Wrap each logical section with `<aap:section id="ID">` and `</aap:section>`.


Output raw code only. No markdown fences, no explanation.