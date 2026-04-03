{
  "protocol": "aap/0.1",
  "id": "product-management-system",
  "version": 2,
  "name": "edit",
  "content": [
    {
      "op": "insert_after",
      "target": {
        "type": "id",
        "value": "controller-layer"
      },
      "content": "package com.example.product.controller;\n\nimport com.example.product.dto.*;\nimport com.example.product.service.ProductService;\nimport jakarta.servlet.http.HttpServletResponse;\nimport jakarta.validation.Valid;\nimport org.springframework.http.HttpHeaders;\nimport org.springframework.http.ResponseEntity;\nimport org.springframework.web.bind.annotation.*;\n\nimport java.io.IOException;\nimport java.io.PrintWriter;\nimport java.util.List;\n\n@RestController\n@RequestMapping(\"/api/products\")\npublic class ProductController {\n    private final ProductService service;\n\n    public ProductController(ProductService service) { this.service = service; }\n\n    @PostMapping\n    public ResponseEntity<ProductResponse> create(@Valid @RequestBody ProductRequest request) {\n        return ResponseEntity.ok(service.createProduct(request));\n    }\n\n    @GetMapping(\"/{id}\")\n    public ResponseEntity<ProductResponse> get(@PathVariable Long id) {\n        return ResponseEntity.ok(service.getProduct(id));\n    }\n\n    @GetMapping(\"/export\")\n    public void exportCsv(HttpServletResponse response) throws IOException {\n        response.setContentType(\"text/csv\");\n        response.setHeader(HttpHeaders.CONTENT_DISPOSITION, \"attachment; filename=\\\"products.csv\\\"\");\n\n        List<ProductResponse> products = service.getAllProducts();\n        PrintWriter writer = response.getWriter();\n        writer.println(\"ID,Name,Price\");\n        for (ProductResponse p : products) {\n            writer.printf(\"%d,%s,%f%n\", p.id(), p.name(), p.price());\n        }\n    }\n}"
    }
  ]
}
"
}],id: