var b = new URL("http://localhost:8532/clip-proxy");

var p = new URLSearchParams();
p.append('target', '{{ path }}');

// Get attributes of the current page.
// Copy the page HTML and URL to the clipboard.
var c = {
    url: document.URL,
    title: document.title,
    userAgent: navigator.userAgent,
    cookieString: document.cookie,
    html: document.documentElement.outerHTML,
};

p.append('title', c.title);
p.append('url', c.url);
p.append('format', '{{ format }}');

// Function to handle clipboard error and make HEAD request
function handleClipboardError(err) {
  console.error("Could not copy text: ", err);
  p.append('clipboardError', err.toString()); // Append error as string

  // Attempt a HEAD request to the page to get the content-type.
  console.log("Attempting to get content-type from HEAD request.");
  var xhr = new XMLHttpRequest();
  xhr.open('HEAD', c.url, true); // Make it asynchronous
  xhr.onreadystatechange = function() {
    if (xhr.readyState === 4) {
      if (xhr.status === 200) {
        p.append('contentType', xhr.getResponseHeader('content-type'));
      } else {
        p.append('contentTypeError', `HEAD request failed with status: ${xhr.status}`);
        console.error(`HEAD request failed with status: ${xhr.status}`);
      }
      // Now that HEAD is done (or failed), open the window
      b.search = p.toString();
      console.log(b.toString());
      window.open(b.toString(), "", "");
    }
  };
  xhr.send();
}

// Function to open the window after clipboard success
function openWindow() {
    b.search = p.toString();
    console.log(b.toString());
    window.open(b.toString(), "", "");
}

// Attempt to copy to clipboard
navigator.clipboard.writeText(JSON.stringify(c))
  .then(() => {
    // Clipboard copy successful
    openWindow();
  })
  .catch(err => {
    // Clipboard copy failed
    handleClipboardError(err);
  });

