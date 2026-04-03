<aap:target id="service-layer">package com.example.product.service;

import com.example.product.dto.*;
import java.util.List;
import java.util.Map;
import java.math.BigDecimal;

public interface ProductService {
    ProductResponse createProduct(ProductRequest request);
    ProductResponse getProduct(Long id);
    List<ProductResponse> getAllProducts();
    <aap:target id="bulk-update-method-decl">void bulkUpdatePrices(Map<Long, BigDecimal> priceUpdates);</aap:target>
}</aap:target>

<aap:target id="service-impl-layer">package com.example.product.service.impl;

import com.example.product.service.ProductService;
import com.example.product.repository.ProductRepository;
import com.example.product.dto.*;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import java.util.List;
import java.util.Map;
import java.math.BigDecimal;

@Service
public class ProductServiceImpl implements ProductService {
    private final ProductRepository repository;

    public ProductServiceImpl(ProductRepository repository) { this.repository = repository; }

    // ... other methods ...

    <aap:target id="bulk-update-method-impl">@Override
    @Transactional
    public void bulkUpdatePrices(Map<Long, BigDecimal> priceUpdates) {
        priceUpdates.forEach((id, newPrice) -> {
            repository.findById(id).ifPresent(product -> {
                product.setPrice(newPrice);
                repository.save(product);
            });
        });
    }</aap:target>
}</aap:target>