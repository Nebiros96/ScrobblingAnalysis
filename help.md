<style>
details {
    background-color: #1e1e1e;
    border-radius: 10px;
    padding: 10px 14px;
    margin-bottom: 8px;
    border: 1px solid #444;
    transition: all 0.3s ease;
}
details:hover {
    border-color: #ff4b4b;
}
summary {
    font-weight: bold;
    cursor: pointer;
    font-size: 16px;
    color: #ff4b4b;
    outline: none;
}
details[open] {
    background-color: #2a2a2a;
}
details p, details b, details br {
    color: #ddd;
}
/* margen entre pregunta y respuesta */
details[open] summary ~ * {
    margin-top: 8px;
    display: block;
}
</style>

#### ⁉️ FAQ

<details>
<summary><b>1. What is Last.fm?</b></summary>
<br>Last.fm is a music tracking platform that logs “scrobbles” the songs you listen to across streaming services, media players, and devices.
<br>It stores your listening history and provides statistics like your most played artists, albums, and tracks.
</details>

<details>
<summary><b>2. What is a Scrobble?</b></summary>
<br>Scrobbling is a term coined by the music platform Last.fm to record and keep track of the music you listen to.  
<br>A Scrobble is counted each time a song is played, as long as more than half of its duration has been reached.
</details>

<details>
<summary><b>3. Why do queries take so long to run?</b></summary>
<br>If your Last.fm history has more than 100k scrobbles, some queries may take several minutes to process.  
This happens because the app needs to fetch large datasets from the Last.fm API, then clean, transform, and calculate metrics locally.  
<br>The more data you have, the more time it takes for each step.
However, you can download a CSV file once you have the complete data, so you don’t have to run everything from scratch
each time you use the app. As a recommendation, avoid modifying the downloadable CSV file, since it can be easily corrupted.”
</details>

<details>
<summary><b>4. How is the data extracted?</b></summary>
<br>The app connects to the official Last.fm API, downloading your listening history in paginated requests (up to 200 scrobbles per call).  
After retrieving the raw data, it’s processed into structured tables for calculations such as streaks, top artists, and activity trends.
</details>

<details>
<summary><b>5. Why don’t my latest scrobbles appear immediately?</b></summary>
<br>Last.fm’s API may take a few minutes to register and expose new scrobbles.  
If you recently listened to music, wait a couple of minutes before refreshing the data.
</details>

<details>
<summary><b>6. May the data differ from what I see on Last.fm’s website?</b></summary>
<br>Yes. The app works with the scrobbles returned by the API.  
<br>Some inconsistencies can happen due to:  
<br>• Deleted or edited scrobbles  
<br>• Timezone differences  
<br>• API limits on historical corrections
</details>

<details>
<summary><b>7. Is my data stored permanently?</b></summary>
<br>No, the app fetches your data on-demand from Last.fm and processes it in memory for visualization.  
Btw, you can download a csv with the data and re-run from where you left off.
</details>

<details>
<summary><b>8. How often can I run queries?</b></summary>
<br>The Last.fm API has rate limits (up to 5 requests per second).  
If you run too many queries (multiple browser tabs) in a short period, the app will slow down or temporarily delay requests to avoid being blocked.
</details>

<details>
<summary><b>9. What features are planned for future development?</b></summary>
<br>• New data visualizations
<br>• Improvements to the user interface
<br>• Code optimizations
</details>

<details>
<summary><b>10. Your code could improve :). Can I contribute to improving the code?</b></summary>
<br>I know, my background is not in Software Development but in Data Science, so my technical perspective is a bit different.
<br>This is actually my first project building an application after years of working with massive SQL queries and BI/DA tools. But hey, everyone starts somewhere! :)
<br>If you’d like to contribute, feel free to reach out — you can find my contact information in the section below.
</details>

---

#### 🔧 Data & Technical Information

- **Primary data source**: Last.fm API (user.getRecentTracks Endpoint)  
- **Data processing**: Python  
- **Graphs**: Plotly  
- **App**: Streamlit  
- **Agent**: Claude Sonnet helped a lot! :)

---

#### ❓ Contact

This dashboard app was built by **Julián Gómez**  
- [LinkedIn](https://www.linkedin.com/in/juliangomez96/)  
- [Instagram](https://www.instagram.com/juliaangomez96/)  

---

Updated: 2025-08-21

