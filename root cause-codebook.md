# Root Causes in Template Engine Application Bugs

## Syntax Misuse (358/1004)
This category captures bugs caused by violations of grammatical rules or syntactic conventions defined by the template engine. 
- **Delimiter Misuse (53):** This category refers to confusion regarding the distinct purposes of various delimiters, leading to incorrect usage or violations of delimiter syntax rules. It involves issues such as unclosed tags, misspelled delimiters, or improper delimiter nesting.
  - `(e.g., "You can’t nest <% %> blocks") (EJS, Post #60225400)`
  - `(e.g., "Syntax error in <%= if flash[:notice]%> Ruby on Rails") (ERB, Post #63495203) `
- **Control Structure Misuse (107):** This category involves violations of the usage specifications for control structures, particularly regarding the incorrect use of tags and filters.
  - `(e.g., "cannot put the extends template tag in an if-else") (Jinja, Post #67490509)`
  - `(e.g., "Where filter allows only to compare a key value with another value.") (Liquid, Post #60424383).`
- **Expression Misuse (198):** This category refers to invalid logic or syntax within expression constructs. It arises when developers employ unsupported expression forms, illegal nesting syntax, or perform incompatible operations on variables.
  - `(e.g., "because you are comparing objects, not strings") (Handlebars.js, Post #75788011)`
  - `(e.g., "Thymeleaf does not support the use of expressions for evaluating URL fragments") (Thymeleaf, Post #69276002)`
  - `(e.g., "You cannot compare asset_class with string") (Django-Template, Post #69039116)`

## Data Transmission Error (209/1004)
- **Incorrect Data (153):** This category involves the binding of incompatible or erroneous data objects to template variables, where the provided data deviates from the structural or type expectations of the template.
  - `(e.g., "When you recur, you are passing the dict itself instead of the iterator") (Jinja, Post #79171202)`
  - `(e.g., "By making sure that the attribute names in the controller and the template were consistent") (Thymeleaf, Post #79079302)`
- **Missing Transmission (56):** This category refers to the omission of required variables from the template context.
  - `(e.g., "You did not pass Post to the context, so indeed the template engine can not render it") (Django-Template, Post #64296665)`
  - `(e.g., "You aren’t passing a body param into your template") (EJS, Post #63541019)`
    
## Improper Configuration (151/1004)
- **Incorrect Resource Reference (67):** This category involves the misconfiguration of static asset directories or the use of invalid reference strategies for external resources (e.g., CSS or images).
  - `(e.g., "Relative references... simply don’t work in emails") (Thymeleaf, Post #67891826)`
  - `(e.g., "we need to set up a public folder for the static content") (EJS, Post #61799209)`
- **Template File Path Misconfiguration (59):** This category refers to errors where the developer specifies incorrect directory paths or filenames for template sources.
  - `(e.g., "Flask by default will only load templates from the root/templates folder") (Jinja, Post #75737273)`
  - `(e.g., "It seems as though you’ve incorrectly placed the file in the wrong folder. Try moving the it into the resources folder") (Thymeleaf, Post #62607540)`
- **Incorrect Template Engine Version (16):** This category refers to failure to align the installed template engine version with the requirements of the existing implementation. Specifically, it arises when the installed template engine introduces breaking changes or deprecations that conflict with the source code.
  - `(e.g., "Upgrading to Haml 5.0 is causing changes due to removal of dynamic quotes functionality") (Haml, Post #60511890)`
- **Improper Format Configuration (9):** This category pertains to the failure to establish correct character encoding or locale-specific formatting rules within the engine configuration.
  - `(e.g., "the character encoding used by your system’s console cannot handle the Persian characters") (Django-Template, Post #75737504)`

## Incorrect Data Use (109/1004)
- **Incorrect Property Access (72):** This category involves the use of incorrect retrieval mechanisms or semantic misunderstandings of data access syntax.
  - `(e.g., "You cannot access the elements of an object by a numeric index") (Blade, Post #60960718)`
  - `(e.g., "When accessing an array or object attributes via foo.bar, Twig won’t try to interpret bar as a variable") (Twig, Post #63140944)`
- **Access Non-existent Properties (37):** This category refers to invalid property references or logic errors in attribute traversal. It involves accessing undefined, null or restricted fields.
  - `(e.g., "there is a variable called {$template} which is not defined") (Smarty, Post #63411125)`
  - `(e.g., "you set your properties as private, and view can not access them") (Blade, Post #66629537)`
## Incompatible Integration (96/1004)
- **Syntax Confusion (34):** This category refers to the erroneous mixing of syntax rules from the host language (e.g., Python, Java), the target format (e.g., HTML), or other engines within the template file.
  - `(e.g., "you can’t use f-strings in Django templates, templates language is not actually a Python") (Django-Template, Post #60376599)`
- **Dependency Misconfiguration (30):** This category involves failures to correctly configure the integration environment, particularly regarding security permissions or external service mappings required by the framework.
  - `(e.g., "You need to allow access to logincss... in the Spring Security configuration") (Thymeleaf, Post #59695497)`
- **Incorrect Requests (25):** This category captures bugs where the template fails to transmit correct data to the host environment via HTTP requests.
  - `(e.g., "your view requires an ID to be passed to the URL") (Django-Template, Post #68948727)`
- **Version Incompatibility (7):** This category arises from compatibility conflicts between the template engine version and its dependent libraries or the underlying framework.
  - `(e.g., "version mismatch between jinja and starlette(fastapi)") (Jinja, Post #73830400)`

## Mechanisms Misunderstanding (81/1004)
- **Parsing Misunderstanding (18): **This category refers to violations of the engine parsing logic resulting from incorrect judgment.
  - `(e.g., "The index has higher precedence compared to the filter") (Jinja, Post #62368279)`
  - `(e.g., "Blade’s compiler will not catch the @error directive inside the mustaches") (Blade, Post #71191222)`
- **Rendering Misunderstanding (35):** This category encompasses failures stemming from unfamiliarity with the engine’s internal principles, resulting in a divergence between expected and actual runtime behaviors
  - **Rendering Timing (14):** confusing the chronological boundary between server-side generation and client-side execution
    - `(e.g., "Liquid... processes the code on the server... value cannot be dynamically updated") (Liquid, Post #78339503)`
  - **Cache Mechanism (7):** causing stale content or inexplicable behaviors due to compilation persistence
  - **Escape (15):** involving misconceptions regarding implicit auto-sanitization rules that lead to unexpected output formats
    - `(e.g., "Jinja2 automatically escapes HTML tags") (Jinja, Post #62984099)`
  - **Others (27):** covering violations of idiosyncratic constraints such as whitespace sensitivity or syntax limitations
    - `(e.g., "Mustache... refers to the fact that there is no straightforward way... to join a list... while omitting a comma at the end") (Mustache, Post #79401259)`


