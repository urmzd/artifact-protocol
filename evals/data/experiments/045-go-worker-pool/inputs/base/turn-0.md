Create a Go worker pool implementation for concurrent task processing.

Include:
- Types: Job interface, Result struct, WorkerPool struct, PoolConfig
- Pool: New, Submit, Start, Stop, Results channel, error handling
- Worker goroutines: process jobs, handle panics, report results
- Example usage: processing a batch of HTTP requests concurrently
- Context cancellation support, graceful shutdown
