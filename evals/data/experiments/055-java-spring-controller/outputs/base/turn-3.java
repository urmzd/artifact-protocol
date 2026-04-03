package com.example.product.repository;

import com.example.product.entity.Product;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

import java.math.BigDecimal;
import java.util.List;

public interface ProductRepository extends JpaRepository<Product, Long> {

    /**
     * Finds products within a specific price range and belonging to a specific category.
     * Note: Assumes a 'category' field exists in the Product entity.
     *
     * @param minPrice Minimum price boundary
     * @param maxPrice Maximum price boundary
     * @param category The category name to filter by
     * @return List of products matching criteria
     */
    @Query("SELECT p FROM Product p WHERE p.price BETWEEN :minPrice AND :maxPrice AND p.category = :category")
    List<Product> findByPriceRangeAndCategory(
        @Param("minPrice") BigDecimal minPrice, 
        @Param("maxPrice") BigDecimal maxPrice, 
        @Param("category") String category
    );

    @Query("SELECT p FROM Product p WHERE (:name IS NULL OR p.name LIKE %:name%) AND (:sku IS NULL OR p.sku = :sku)")
    org.springframework.data.domain.Page<Product> search(
        @Param("name") String name, 
        @Param("sku") String sku, 
        org.springframework.data.domain.Pageable pageable
    );
}