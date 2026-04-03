# Experiment: html-blog-post

**Format:** text/html | **Size:** medium | **Edits:** 3

**Expected sections:** header, article-content, author-bio, comments

## Protocol cost (the only difference from base)

| Prompt | Chars | ~Tokens |
|---|---|---|
| Base system | 90 | 22 |
| AAP init system | 226 | 56 |
| AAP maintain system | 379 | 94 |
| **Protocol overhead** | | **~128 tokens** |

## Turns

| Turn | Edit |
|---|---|
| 0 | (creation) |
| 1 | Change the article title to 'Building Scalable Microservices with Go and gRPC' |
| 2 | Rewrite the comments section to have 6 comments instead of 4, with replies ne... |
| 3 | Add a 'Related Articles' section after the author bio showing 3 related artic... |