---
layout: default
title: Plugins
nav_order: 10
---

# Plugins

The plugin system is still in **beta** for now.

## Supported Plugins

The plugins are used to extend the functionality of the wiki. Most of them are accessible through the use of `tags`.
For now there are only a few supported.  

###Drawio plugin
Allows you to add an **interactive drawio drawing** to the wiki. Use `[[draw]]` 
tag to insert a drawio block, that can be edited in page preview mode.

###Alerts
Allows to insert an alert message in the page text. Here is a list of 
possible alert messages:
- `[[info]]`
- `[[warning]]`
- `[[danger]]`
- `[[success]]`

###Embedded pages
Allows to show another page in the current one.<br> Usage:<br>`[[page: some-page]]`<br> where `some-page`
is the name of another page from the wiki

###Swagger integration
Allows to insert a **swagger** block into the wiki page. <br> Usage: <br> 
`[[swagger link]]` 
<br>
where `link` is a link to a GET endpoint with .json openapi file.
<br>
`[[swagger https://petstore3.swagger.io/api/v3/openapi.json]]` can be used as an example.

###Plantuml diagrams
Allows to embed a plantuml diagram. 
<br>Usage:<br>

\`\`\`plantuml
@startuml
Alice -> Bob: Authentication Request
Bob --> Alice: Authentication Response

Alice -> Bob: Another authentication Request
Alice <-- Bob: Another authentication Response
@enduml
\`\`\`
<br>

A custom plantuml server can be defined using configuration file.
Read more about plantuml [here](https://plantuml.com).

###Mermaid diagrams
Allows to embed a mermaid diagram.
<br>Usage:<br>
\`\`\`mermaid
graph LR
A[Square Rect] -- Link text --> B((Circle))
A --> C(Round Rect)
B --> D{Rhombus}
C --> D
\`\`\`
<br>
Read more about mermaid diagrams [here](https://mermaid.js.org/intro/).
