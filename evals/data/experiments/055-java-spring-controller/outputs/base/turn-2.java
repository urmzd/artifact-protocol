package com.example.product.service;

import com.example.product.entity.Product;
import com.example.product.model.*;
import com.example.product.repository.ProductRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.cache.annotation.CacheEvict;
import org.springframework.cache.annotation.Cacheable;
import org.springframework.data.domain.*;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.math.BigDecimal;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

@Service
@RequiredArgsConstructor
public class ProductService {
    private final ProductRepository repository;

    @Cacheable(value = "products", key = "#id")
    public ProductResponse getById(Long id) {
        Product p = repository.findById(id).orElseThrow(() -> new RuntimeException("Product not found"));
        return new ProductResponse(p.getId(), p.getName(), p.getSku(), p.getPrice());
    }

    /**
     * Updates multiple product prices in a single transaction.
     * Clears the 'products' cache after the operation.
     * 
     * @param priceUpdates A map of Product ID to new Price
     */
    @Transactional
    @CacheEvict(value = "products", allEntries = true)
    public void bulkUpdatePrices(Map<Long, BigDecimal> priceUpdates) {
        List<Product> products = repository.findAllById(priceUpdates.keySet());
        
        for (Product product : products) {
            BigDecimal newPrice = priceUpdates.get(product.getId());
            if (newPrice != null) {
                product.setPrice(newPrice);
            }
        }
        repository.saveAll(products);
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