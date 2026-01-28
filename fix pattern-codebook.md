# Fix Patterns in Template Engine Application Bugs

## Environment (112/982)
- **Modify Template Engine Configuration (42):** This pattern involves adjusting global settings to satisfy feature prerequisites.
  - `(e.g., "To fix this issue, you can set the default encoding to UTF-8 in your Django settings.py file” (Django-Template, Post #75737504)`
  - `(e.g., "You might try this answer to disable the view cache") (EJS, Post #61377755)`
- **Change Template File Path (51):** This pattern addresses template resolution failures by rectifying the physical location of files or their reference paths.
  - `(e.g., "Typically you write the name of the app under the templates directory") (Django-Template, Post #66955884)`
  - `(e.g., "you named header.handlebars change it to head.hbs") (Handlebars.js, Post #62785112)`
- **Change version (13):** This pattern involves resolving dependency conflicts or feature mismatches by adjusting the version of the template engine or its associated libraries.
  - `(e.g., "So if you’re using Twig 1, upgrade it at least to v1.43.0") (Twig, Post #61609531)`
- **Clear Cache (6):** This pattern involves removing cached data to force the engine to re-render. It resolves issues where the caching mechanism persists outdated outputs, preventing recent code or data changes from taking effect.
  - `(e.g., "Clear Laravel view’s cache") (Blade, Post #71175806)`

## Template (666/980)
- **Fix Template Logic (315):** This pattern involves correcting semantic or logical errors within the template’s control flow and expressions. Unlike syntax fixes, the code is grammatically correct but functionally wrong. It encompasses using appropriate tags/filters, correcting operation precedence in expressions, or handling client-side vs. server-side execution timing.
  - `(e.g., "I added string filters to build the url") (Liquid, Post #74052469)`
  - `(e.g., "You can use interpolation") (Pug, Post #66732888)`
- **Fix Template Syntax (172):** This pattern addresses syntax errors in the template language. It involves correcting typos, improper delimiters, or malformed constructs that prevent the parser from processing the file.
  - `(e.g., “You have to put it with double quotes... also you should use <%- for includes”) (EJS, Post #59979886)`
- **Fix Data Access Way (66):** This pattern involves modifying the data access method used to fetch data from context variables.
  - `(e.g., "You should be able to access the related GeoHazard and Assessment objects by their related_name") (Django-Template, Post #72771164)`
- **Fix Resource Reference Path (61):** This pattern corrects incorrect reference paths for static assets (CSS, JavaScript, images).
  - `(e.g., "You should use css link relative to root like ’/css/styles.css’") (Handlebars.js, Post #59708405)`
- **Simplify Logics in Template (30):** This pattern involves moving complex computations from the template to the application backend.  It adheres to the principle of Separation of Concerns by ensuring that heavy logic (e.g., calculations, complex filtering) is handled by the host language rather than the presentation layer. Unlike Fix Application Logic, this represents a refactoring effort
  - `(e.g., "I suggest you to do the calculations in views.py, save them into variables and then pass it to template") (Django-Template, Post #64151516)`
  - `(e.g., "I would suggest creating a new Handlebars Helper to compare Object IDs") (Handlebars.js, Post #75788011)`
- **Check Validity (22):** This pattern introduces conditional checks (defensive programming) to verify the existence or state of variables before use. It prevents runtime errors by checking if a variable is defined, not null, or satisfies specific constraints prior to rendering.
  - `(e.g., "In your jinja template first check to see if the value is set, and then if it is include it") (Jinja, Post #60139470)`
## ApplIcation (204/982)
- **Fix Application Logic (65):** This pattern involves rectifying defects in the control flow or architectural implementation of the backend application. It addresses scenarios where the application’s processing sequence or business logic is fundamentally incorrect, requiring structural modifications.
  - `(e.g. "In your controller, you should be using standard PHP concatenation") (Blade, Post #67957147)`
  - `(e.g., "You may move the JAVA calls into your controller and put the result into the view model") (Thymeleaf, Post #66048129)`
- **Repair Transfered Data (139):** This pattern focuses on adjusting the data preparation logic to ensure the context passed to the template matches its expectations. Unlike logic fixes, the overall control flow here is generally correct, but the specific data objects contain errors in type, structure, or visibility.
  - `(e.g., "but to stringify it: res.render("favorites", JSON.stringgify(data: print: favorites, page: true))") (EJS, Post #63663849)`
  - `(e.g., "you should pass it as a local") (ERB, Post #61521805)`
