# Symptoms in Template Engine Application Bugs

## Initialization Error (77/1004)
This category involves situations where environmental or configuration issues prevent the template engine from starting or functioning correctly.
- **Template Not Found (60):** The engine cannot locate or access the template file due to path or resolver misconfiguration.
  - `(e.g., "template might not exist or might not be accessible by any of the configured Template Resolvers") (Thymeleaf, Post#72406562)`
- **Dependency Error (17):** The template engine and related dependencies are not installed, or are installed with wrong version, or are not correctly integrated.
  - `(e.g., "I am getting the error-ImportError: cannot import name 'escape' from 'jinja2'".) (Jinja, Post#71718167)`

## Compilation Error (238/1004)
This category contains various syntax errors that the template engine throws when parsing the template.
- **Bad Delimiter (47):** The template uses mismatched,  mismatched, missing, or incorrectly formatted syntax delimiters (e.g., interpolation symbols, directive symbols) used in the template.
  - `(e.g., "Could not find matching close tag for "<%".") (EJS, Post#60225400)`
- **Unrecognized Control Structure (38):** The template engine fails to recognize control strutures in the template, such as tags, and filters.
  - `(e.g., "'mes_tags' is not a registered tag library.") (Django-Template, Post #59932340)`
- **Invalid Expression (153):** The template engine fails to parse expressions in the template, such as interpolation expressions, conditional expressions, and arithmetic expressions.
  - `(e.g., TemplateSyntaxError at /show_all. Could not parse the remainder: '[num]' from 'roles[num]') (Django-Template, Post#74484522)`

## Placeholder Error (181/1004)
This category refers to data-flow failures arising from discrepancies between the data provided by the host environment and the usage expectations of the template.
- **Type Mismatch(48):** The data type of the passed value is incompatible with the operations required by the template.
  - `(e.g., "datetime.date object is not iterable") (Django-Template, Post#77934119)`
- **Undefined Variable (78):** This error occurs when the rendering engine is unable to resolve a value for a specific placeholder from the provided data context, typically due to the variable being missing or improperly named in the host environment.
  - `(e.g., "Undefined variable: title") (Blade, Post#61484068)`
- **Property Access Error (55):** Failures occurring when attempting to access nonexistent attributes, out-of-bounds indices, or restricted resources.
  - `(e.g., "Property or field ’author’ cannot be found on null") (Thymeleaf, Post #6422464))`

## Abnormal Rendering Results (465/1004)
This category
- **Blank Output (113):** The rendered output is blank.
  - `(e.g., "partner.title does not grab the Post Title, it’s blank") (Twig, Post #61805121)`
- **Unexpected Output (267):** The renderred output is not blank, but does not meet the developer's expectations.
  - `(e.g., "The output of this is foo while the expected output is bar") (Liquid, Post #68623329)`
- **Resource Not Found (76):** This symptom pertains to failures in retrieving or loading static assets within the rendered output, which manifests in two distinct forms. Explicit loading failures are characterized by specific error logs. In contrast, silent rendering issues occur when assets fail to appear in the final presentation without triggering system errors.
  - `(e.g.,"GET .../images/normal.gif 404 (Not Found)") (Handlebars.js, Post #71242969)`
  - `(e.g., "the user.jpg image is not displayed in the email, instead the raw code is displayed") (Pug, Post #79520210)`
- **Broken HTML Elements (9):** This category describes structural or functional defects observed in the generated DOM elements. It includes cases where UI components fail to render, appear as raw object representations, or lose their interactive functionality.
  - `(e.g., "but then when I return a new view of the page, divs with my checkboxes do not appear") (Thymeleaf, Post #66610802)` 
  - `(e.g., "pagination buttons... don’t work or go anywhere") (Twig,Post #76181742)`

## Others (43/1004)
This category comprises atypical bugs that cannot be classified into any other specific symptom. It includes issues such as URL reverse routing failures and 404 errors. `(e.g., "Reverse for ’section’ with arguments ’(",)’ not found") (Django-Template, Post #68303980)`.
