# Drivesearch: A deployable Google Docs add-on for semantic search in your Drive folder

I made this app because I wanted to try out document search. For a more in-depth discussion, please see the technical blog post I've written: https://shariarvg.github.io/drivesearch/.

This README will give you some background on the repo, in case you decide to customize it and deploy your own version. When you're ready to see your changes (e.g. a different embedding function) in action, go ahead and deploy the Flask app defined in app.py. This app has three functionalities:

1. **Obtaining user credentials for Google Drive and OAuth2 access.** We need to be able to view, download, edit, and create files in the users Drive (as for the last two functionalities, they will be constrained to a single file where we store representations of all the files in their folder), more on this below
2. **Maintaining a meta-database that tracks each file in the user's Drive.** All we're doing here is applying our representation (or embedding function) to each file in the user's Drive and storing them in a pickle file, which we write to their Drive for security. Ideally, there's a CRON job running that will check for updates (new and modified files) to update the database.
3. **Query execution**: This starts in the Google Docs add-on, where the query is sent into Flask and then embedded in the backend. After that, the meta-database is pulled, and a similarity search is used to identify the matching documents, which are passed back in the form of file ID's.

## Configuring a Google Docs add-on

The following code defines the sidebar, which is where code will typically get stored. The file I have is called sidebar.html.

<pre lang = 'markdown'>

```html <!DOCTYPE html>
<html>
  <head>
    <base target="_top">
  </head>
  <body>
    <h3>Drive Search</h3>
    <input type="text" id="query" placeholder="Enter your search..." />
    <button onclick="authorize()">Authorize Access</button>

    <script>
    function authorize() {
      const fullEmail = Session.getActiveUser().getEmail();  // Must be passed from Apps Script
      const username = fullEmail.split("@")[0];
      const url = `https://your-app.onrender.com/authorize?username=${encodeURIComponent(username)}`;
      window.open(url, "_blank");
    }
    </script>

    <button onclick="search()">Search</button>
    <div id="results" style="margin-top:1em;"></div>

    <script>
      function search() {
        const query = document.getElementById('query').value;
        google.script.run.withSuccessHandler(displayResults).searchDocs(query);
      }

      function displayResults(results) {
        const container = document.getElementById('results');
        container.innerHTML = '';
        if (results.length === 0) {
          container.innerText = "No results found.";
        } else {
          results.forEach(r => {
            const link = document.createElement('a');
            link.href = r.url;
            link.innerText = r.name;
            link.target = '_blank';
            container.appendChild(link);
            container.appendChild(document.createElement('br'));
          });
        }
      }
    </script>
  </body>
</html>
```
</pre>

Below, I paste in the Code.gs file that's also necessary for a Google app.

<pre lang = 'markdown'>```javascript
function onOpen() {
  DocumentApp.getUi()
    .createMenu('Drive Search')
    .addItem('Open Sidebar', 'showSidebar')
    .addToUi();
}

function showSidebar() {
  const html = HtmlService.createHtmlOutputFromFile('sidebar')
    .setTitle('Drive Search');
  DocumentApp.getUi().showSidebar(html);
}

function searchDriveSemantically(query) {
  const fullEmail = Session.getActiveUser().getEmail();
  const username = fullEmail.split("@")[0];

  const response = UrlFetchApp.fetch("https://drivesearch.onrender.com/search", {
    method: "post",
    contentType: "application/json",
    payload: JSON.stringify({
      query: query,
      username: username,
      k: 5
    }),
    muteHttpExceptions: true
  });

  const result = JSON.parse(response.getContentText());
  return result;
}```

</pre>

Finally, the appsscript.json 

<pre lang = 'markdown'>```json
{
  "timeZone": "America/New_York",
  "exceptionLogging": "STACKDRIVER",
  "oauthScopes": [
    "https://www.googleapis.com/auth/documents.currentonly",
    "https://www.googleapis.com/auth/drive.readonly",
    "https://www.googleapis.com/auth/script.container.ui"
  ]
}```
</pre>