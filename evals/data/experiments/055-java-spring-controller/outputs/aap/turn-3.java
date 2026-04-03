<aap:target id="repository-layer">package com.example.product.repository;

import com.example.product.model.Product;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import java.math.BigDecimal;
import java.util.List;

public interface ProductRepository extends JpaRepository<Product, Long> {

    <aap:target id="find-by-price-range-and-category-method">@Query("SELECT p FROM Product p WHERE p.price BETWEEN :minPrice AND :maxPrice AND p.category = :category")
    List<Product> findByPriceRangeAndCategory(@Param("minPrice") BigDecimal minPrice, 
                                             @Param("maxPrice") BigDecimal maxPrice, 
                                             @Param("category") String category);</aap:target>
}</aap:target>