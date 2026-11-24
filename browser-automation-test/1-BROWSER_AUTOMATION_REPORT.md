# Browser Automation Capability Test: report
Date: 2026-11-24. Sites: https://the-internet.herokuapp.com (public test site) and https://quotes.toscrape.com/js/ (public scraping practice site). No login, no form submission, no transactions.

## Answers
- **Did I use a real browser?** Yes. Pages were driven in a live Chrome-based browser: it ran page JavaScript (`document.readyState` complete, DOM changed after clicks), rendered the pages and produced PNG screenshots. HTTP-only fetches could not show those results (see http_comparison.txt).
- **Interactions that worked (all logged in browser_interaction_log.txt):**
  1. Page load verified: home page title "The Internet", readyState complete, 81 links.
  2. Clicks: 3 clicks on "Add Element" created 3 delete buttons (counted in the DOM).
  3. Dropdown: selected "Option 2"; the select's value became "2" (screenshot_1).
  4. Hover menu: hovering "Enabled" changed the visible menu items from 2 to 4.
  5. Navigation: clicked a link from the home page and landed on /challenging_dom; clicked "Next" on the quotes site and landed on /js/page/2/.
  6. Data extraction: read the table header (Lorem, Ipsum, Dolor, Sit, Amet, Diceret, Action) and first row (Iuvaret0, Apeirian0, ...); read 10 quotes on the JavaScript-rendered quotes page.
  7. Screenshots: 3 PNG files saved (screenshot_1..3).
  8. Slow loading: on /dynamic_loading/2 the result element was absent right after clicking Start; waiting for the text matched after about 5 s and showed "Hello World!" (screenshot_3).
  9. HTTP vs browser comparison: http_comparison.txt.
- **What did not work or was not proven:**
  - File download: I clicked the download link and the page stayed on /download, but I could NOT retrieve a downloaded file from the browser's download folder. I verified the file instead by a browser-side fetch (200, 5 bytes) and a direct HTTP GET; test_download_19.json is the HTTP copy: a plain 5-byte text payload ("sdfsd"), not valid JSON despite the .json name, and not a file saved by the click.
  - /slow server page: it loaded in 369 ms today, so a truly slow server page was not tested; only a JavaScript-delayed element was.
  - Page 2 of the quotes site: the URL changed to /js/page/2/ but my first-quote read returned null (probably read before the JavaScript finished); I did not re-read it, so only the navigation is confirmed.
  - Menu item names: my text extraction for the menu was poor, so only the visible count (2 to 4) is proven, not the item labels.
  - Canvas number "96326" is read from the screenshot, not extracted by code.
- **Can I handle JavaScript?** Yes: JS-rendered content (quotes, delayed element, hover menu, added buttons) appeared in the browser and not in plain HTTP. I can also run small JavaScript reads inside a page.
- **Can I keep a browser session?** Tested behaviour only: a cookie I set (audit_test) stayed available while moving between pages in the same session. After I closed the session and opened a new one, the cookie was gone. So within one session, yes; across sessions, not for this test (no login saved, since I did not sign in). Whether a signed-in session would persist was not tested.

## Evidence files
browser_interaction_log.txt (timestamped steps), http_comparison.txt, screenshot_1_dropdown_option2.png, screenshot_2_challenging_dom.png, screenshot_3_dynamic_loaded.png, test_download_19.json.

## Limits of this test
One session on two public demo sites. Results show these interactions work on these sites; they are not a guarantee for every site (sites that block automation or need logins were not tested).
