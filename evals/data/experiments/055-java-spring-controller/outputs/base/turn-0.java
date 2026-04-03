package com.example.product.model;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Positive;
import java.math.BigDecimal;

public record ProductRequest(
    @NotBlank(message = "Name is required") String name,
    @NotBlank(message = "SKU is required") String sku,
    @NotNull @Positive BigDecimal price
) {}

package com.example.product.model;

import java.math.BigDecimal;

public record ProductResponse(Long id, String name, String sku, BigDecimal price) {}

package com.example.product.model;

public record ProductSearchCriteria(String name, String sku, Integer page, Integer size, String sortBy) {}

package com.example.product.model;

import java.util.List;

public record PagedResponse<T>(List<T> content, long totalElements, int page, int totalPages) {}

package com.example.product.entity;

import jakarta.persistence.*;
import lombok.*;

@Entity
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
public class Product {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;
    private String name;
    @Column(unique = true)
    private String sku;
    private java.math.BigDecimal price;
}

package com.example.product.repository;

import com.example.product.entity.Product;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

public interface ProductRepository extends JpaRepository<Product, Long> {
    @Query("SELECT p FROM Product p WHERE (:name IS NULL OR p.name LIKE %:name%) AND (:sku IS NULL OR p.sku = :sku)")
    Page<Product> search(@Param("name") String name, @Param("sku") String sku, Pageable pageable);
}

package com.example.product.service;

import com.example.product.entity.Product;
import com.example.product.model.*;
import com.example.product.repository.ProductRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.cache.annotation.CacheEvict;
import org.springframework.cache.annotation.Cacheable;
import org.springframework.data.domain.*;
import org.springframework.stereotype.Service;

import java.util.stream.Collectors;

@Service
@RequiredArgsConstructor
public class ProductService {
    private final ProductRepository repository;

    @Cacheable(value = "products", key = "#id")
    public ProductResponse getById(Long id) {
        Product p = repository.findById(id).orElseThrow(() -> new RuntimeException("Not found"));
        return new ProductResponse(p.getId(), p.getName(), p.getSku(), p.getPrice());
    }

    public PagedResponse<ProductResponse> search(ProductSearchCriteria criteria) {
        Pageable pageable = PageRequest.of(criteria.page() != null ? criteria.page() : 0, 
                                          criteria.size() != null ? criteria.size() : 10, 
                                          Sort.by(criteria.sortBy() != null ? criteria.sortBy() : "name"));
        Page<Product> page = repository.search(criteria.name(), criteria.sku(), pageable);
        return new PagedResponse<>(
            page.getContent().stream().map(p -> new ProductResponse(p.getId(), p.getName(), p.getSku(), p.getPrice())).collect(Collectors.toList()),
            page.getTotalElements(), page.getNumber(), page.getTotalPages()
        );
    }

    @CacheEvict(value = "products", allEntries = true)
    public ProductResponse create(ProductRequest req) {
        Product p = new Product(null, req.name(), req.sku(), req.price());
        p = repository.save(p);
        return new ProductResponse(p.getId(), p.getName(), p.getSku(), p.getPrice());
    }
}

package com.example.product.controller;

import com.example.product.model.*;
import com.example.product.service.ProductService;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/products")
@RequiredArgsConstructor
public class ProductController {
    private final ProductService service;

    @GetMapping("/{id}")
    public ResponseEntity<ProductResponse> get(@PathVariable Long id) {
        return ResponseEntity.ok(service.getById(id));
    }

    @GetMapping
    public ResponseEntity<PagedResponse<ProductResponse>> search(ProductSearchCriteria criteria) {
        return ResponseEntity.ok(service.search(criteria));
    }

    @PostMapping
    public ResponseEntity<ProductResponse> create(@Valid @RequestBody ProductRequest request) {
        return ResponseEntity.ok(service.create(request));
    }
}

package com.example.product.exception;

import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.ControllerAdvice;
import org.springframework.web.bind.annotation.ExceptionHandler;

@ControllerAdvice
public class GlobalExceptionHandler {
    @ExceptionHandler(RuntimeException.class)
    public ResponseEntity<String> handle(RuntimeException ex) {
        return ResponseEntity.status(404).body(ex.getMessage());
    }
}