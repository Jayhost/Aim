using MyBlazorApp.Components;

var builder = WebApplication.CreateBuilder(args);

// Add services to the container.
builder.Services.AddRazorComponents()
    .AddInteractiveServerComponents();

builder.Services.AddHttpClient();

var app = builder.Build();

// Configure the HTTP request pipeline.
if (!app.Environment.IsDevelopment())
{
    app.UseExceptionHandler("/Error", createScopeForErrors: true);
    // The default HSTS value is 30 days. You may want to change this for production scenarios, see https://aka.ms/aspnetcore-hsts.
    app.UseHsts();
}

app.UseHttpsRedirection();

app.UseStaticFiles();
app.UseAntiforgery();

app.MapRazorComponents<App>()
    .AddInteractiveServerRenderMode();

// --- START: Add Reverse Proxy for llama.cpp ---
// --- This is the new code you will add here. ---

// Define the base address for the llama.cpp server
var llamaApiBaseAddress = "http://host.docker.internal:8000";

// Create a dedicated HttpClient for our proxy
var proxyHttpClient = new HttpClient { BaseAddress = new Uri(llamaApiBaseAddress) };

// This is our new reverse proxy endpoint for the chat
app.MapPost("/api/chat", async (HttpContext context) =>
{
    // Create a new request to forward to the llama.cpp server
    var forwardRequest = new HttpRequestMessage(HttpMethod.Post, "/completion");
    
    // Copy the body from the incoming request to the forward request
    forwardRequest.Content = new StreamContent(context.Request.Body);
    forwardRequest.Content.Headers.ContentType = new System.Net.Http.Headers.MediaTypeHeaderValue("application/json");

    // Send the request and get the response headers first
    using var response = await proxyHttpClient.SendAsync(forwardRequest, HttpCompletionOption.ResponseHeadersRead, context.RequestAborted);

    // Copy the status code from the llama.cpp response to our response
    context.Response.StatusCode = (int)response.StatusCode;

    // This is the magic part: we stream the content directly back to the client
    // without waiting for it to finish.
    await response.Content.CopyToAsync(context.Response.Body, context.RequestAborted);
});

app.Run();
