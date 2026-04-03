package com.example.product.controller;

import com.example.product.entity.Product;
import com.example.product.repository.ProductRepository;
import jakarta.servlet.http.HttpServletResponse;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.io.IOException;
import java.io.PrintWriter;
import java.util.List;

@RestController
@RequestMapping("/api/products")
@RequiredArgsConstructor
public class ProductExportController {

    private final ProductRepository repository;

    /**
     * Exports all products to a CSV file.
     * 
     * @param response HttpServletResponse to set headers and write output
     * @throws IOException if an I/O error occurs
     */
    @GetMapping("/export")
    public void exportToCsv(HttpServletResponse response) throws IOException {
        response.setContentType("text/csv");
        response.setHeader("Content-Disposition", "attachment; filename=\"products.csv\"");

        List<Product> products = repository.findAll();

        try (PrintWriter writer = response.getWriter()) {
            writer.println("ID,Name,SKU,Price");
            for (Product p : products) {
                writer.printf("%d,%s,%s,%s%n", 
                    p.getId(), 
                    escapeCsv(p.getName()), 
                    escapeCsv(p.getSku()), 
                    p.getPrice());
            }
        }
    }

    private String escapeCsv(String data) {
        if (data == null) return "";
        return "\"" + data.replace("\"", "\"\"") + "\"";
    }
}