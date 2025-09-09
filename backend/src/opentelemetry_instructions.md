# **Comprehensive Guide to OpenTelemetry Instrumentation**

This guide provides a step-by-step process for instrumenting Python code that uses FastAPI, StreamingResponse, and asynchronous generators with OpenTelemetry.

### **Key Concepts**

  * **Trace**: A trace represents a single request or operation as it moves through a system.
  * **Span**: A span is a unit of work within a trace. Each span has a start time, end time, and attributes (key-value pairs) that provide context.
  * **Tracer**: An object used to create spans.
  * **Asynchronous Generator**: A Python function that uses `async def` and `yield` to stream data. The `yield` statements pause the function and send data, and the function's execution continues on the next call.

### **The Challenge with Streaming Responses**

When using an `AsyncGenerator` with FastAPI's `StreamingResponse`, the default OpenTelemetry instrumentation for FastAPI closes the request span at the first `yield`. This is because the framework returns the generator object at that point, which is interpreted as the function's "completion." This results in an incorrect trace duration that does not reflect the entire time spent on the streaming process.

### **Solution: Manual Span Management**

To solve this, you must manually manage a new span that is a child of the main request span. This new span will encapsulate the entire duration of the asynchronous generator, ensuring accurate timing.

### **Step-by-Step Instructions**

1.  **Import Necessary Libraries**: Ensure you have `opentelemetry` and `opentelemetry-api` installed. Import the `tracer` and `SpanKind` from `opentelemetry`.

2.  **Define the Tracer**: In your module, initialize the tracer.

    ```python
    from opentelemetry import trace
    from opentelemetry.trace import SpanKind

    tracer = trace.get_tracer(__name__)
    ```

3.  **Modify the Asynchronous Generator Function**:

      * **Remove any decorators** like `@tracer.start_as_current_span` from your generator function. These decorators are not suitable for this use case.
      * **Add a `with` statement** inside the function's body to create a new span. This span will be a child of the parent request span, as `start_as_current_span` automatically inherits the context of the active span.
      * Set **descriptive attributes** on the new span to provide context about the operation.

    <!-- end list -->

    ```python
    async def my_streaming_generator(...):
        # The 'with' block is the key.
        # It ensures the span remains open for the entire duration of the generator.
        with tracer.start_as_current_span(
            "my_streaming_operation",
            kind=SpanKind.SERVER,
        ) as span:
            # Add relevant attributes to the span
            span.set_attribute("my.operation.id", "some-unique-id")
            
            # This is where you will add your code
            yield "first chunk"

            # The span remains open during any further logic or yields
            await some_async_work()
            yield "second chunk"

            # The span will automatically end here, when the generator is exhausted.
    ```

4.  **Call the Generator from a FastAPI Endpoint**: Your FastAPI endpoint should simply return a `StreamingResponse` that uses your generator. No special instrumentation is needed here, as the manual span management is already handled inside the generator. The automatic FastAPI instrumentation will create the parent span.

    ```python
    from fastapi import FastAPI
    from fastapi.responses import StreamingResponse

    app = FastAPI()

    @app.get("/stream")
    async def stream_endpoint():
        return StreamingResponse(my_streaming_generator(), media_type="text/plain")
    ```

### **Summary of the Process**

1.  The FastAPI request starts. OpenTelemetry's automatic instrumentation creates a parent span.
2.  The FastAPI endpoint calls your generator function.
3.  Inside your generator, a new span is created with `with tracer.start_as_current_span(...)`. This new span is automatically linked as a child of the parent span.
4.  The generator yields chunks of data. The `StreamingResponse` sends these chunks to the client. The new span remains open during this entire process.
5.  The generator finishes. The `with` block is exited, and the new span is ended and reported to the OpenTelemetry Collector.
6.  The FastAPI request ends, and the parent span is also ended.

This two-span structure—a parent span for the overall request and a child span for the streaming operation—provides an accurate and complete trace of the request.