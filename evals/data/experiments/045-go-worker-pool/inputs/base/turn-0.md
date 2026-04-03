Create a Go worker pool implementation for concurrent task processing.

Include:
- Types: Job interface, Result struct, WorkerPool struct, PoolConfig
- Pool: New, Submit, Start, Stop, Results channel, error handling
- Worker goroutines: process jobs, handle panics, report results
- Example usage: processing a batch of HTTP requests concurrently
- Context cancellation support, graceful shutdown

Use section IDs: types, pool, workers, example

Use AAP section markers to delineate each major code block.
Wrap each logical section with `<aap:section id="ID">` and `</aap:section>`.


Output raw code only. No markdown fences, no explanation.