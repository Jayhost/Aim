// content.js - Extracts page content
(function() {
    // Listen for messages from the sidebar
    browser.runtime.onMessage.addListener((message, sender, sendResponse) => {
        if (message.action === "getPageContent") {
            const content = extractPageContent();
            sendResponse({
                content: content,
                url: window.location.href,
                title: document.title
            });
        }
        return true; // Keep channel open for async response
    });

    function extractPageContent() {
        // Clone the body to avoid modifying the actual page
        const clone = document.body.cloneNode(true);
        
        // Remove scripts, styles, and other non-content elements
        const unwanted = clone.querySelectorAll(
            'script, style, nav, header, footer, iframe, .ad, .advertisement, [role="banner"], [role="navigation"]'
        );
        unwanted.forEach(el => el.remove());
        
        // Get text content
        let text = clone.innerText || clone.textContent;
        
        // Clean up whitespace
        text = text.replace(/\s+/g, ' ').trim();
        
        // Limit to ~10000 characters to avoid overwhelming the LLM
        return text.substring(0, 10000);
    }
})();