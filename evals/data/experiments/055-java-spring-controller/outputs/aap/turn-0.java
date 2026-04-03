<aap:target id="product-management-package">
package com.example.product.api;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.cache.annotation.EnableCaching;

@SpringBootApplication
@EnableCaching
public class ProductApplication {
    public static void main(String[] args) {
        SpringApplication.run(ProductApplication.class, args);
    }
}
</aap:target>

<aap:target id="dto-package">
package com.example.product.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Positive;
import java.math.BigDecimal;

public record ProductRequest(@NotBlank String name, @Positive BigDecimal price) {}
public record ProductResponse(Long id, String name, BigDecimal price) {}
public record ProductSearchCriteria(String nameQuery, Integer page, Integer size, String sortBy) {}
public record PagedResponse<T>(java.util.List<T> content, long totalElements, int page) {}
</aap:target>

<aap:target id="repository-layer">
package com.example.product.repository;

import com.example.product.model.Product;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

@Repository
public interface ProductRepository extends JpaRepository<Product, Long> {
    Page<Product> findByNameContainingIgnoreCase(String name, Pageable pageable);
}
</aap:target>

<aap:target id="service-layer">
package com.example.product.service;

import com.example.product.dto.*;
import com.example.product.model.Product;
import com.example.product.repository.ProductRepository;
import org.springframework.cache.annotation.CacheEvict;
import org.springframework.cache.annotation.Cacheable;
import org.springframework.data.domain.*;
import org.springframework.stereotype.Service;

@Service
public class ProductService {
    private final ProductRepository repository;

    public ProductService(ProductRepository repository) { this.repository = repository; }

    @Cacheable(value = "products", key = "#id")
    public ProductResponse getProduct(Long id) {
        Product p = repository.findById(id).orElseThrow();
        return new ProductResponse(p.getId(), p.getName(), p.getPrice());
    }

    @CacheEvict(value = "products", allEntries = true)
    public ProductResponse createProduct(ProductRequest req) {
        Product p = repository.save(new Product(req.name(), req.price()));
        return new ProductResponse(p.getId(), p.getName(), p.getPrice());
    }
}
</aap:target>

<aap:target id="controller-layer">
package com.example.product.controller;

import com.example.product.dto.*;
import com.example.product.service.ProductService;
import jakarta.validation.Valid;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/products")
public class ProductController {
    private final ProductService service;

    public ProductController(ProductService service) { this.service = service; }

    @PostMapping
    public ResponseEntity<ProductResponse> create(@Valid @RequestBody ProductRequest request) {
        return ResponseEntity.ok(service.createProduct(request));
    }

    @GetMapping("/{id}")
    public ResponseEntity<ProductResponse> get(@PathVariable Long id) {
        return ResponseEntity.ok(service.getProduct(id));
    }
}
</aap:target>

<aap:target id="exception-handling">
package com.example.product.exception;

import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

@ControllerAdvice
public class GlobalExceptionHandler {
    @ExceptionHandler(Exception.class)
    public ResponseEntity<String> handleGeneral(Exception e) {
        return ResponseEntity.internalServerError().body(e.getMessage());
    }
}
</aap:target>