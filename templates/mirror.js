// This script copies details about the page into the clipboard.
var b = new URL("http://localhost:8532/clip-proxy");

var p = new URLSearchParams();
p.append('target', '{{ path }}');

// Get attributess of the current page.
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

navigator.clipboard.writeText(JSON.stringify(c)).then(
  function () {
    // alert('Page HTML copied to clipboard.');
  },
  function (err) {
    console.error("Could not copy text: ", err);
  }
);

b.search=p.toString();
console.log(b.toString());

w=window.open(b.toString(),"","");
