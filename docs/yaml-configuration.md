---
layout: default
title: Configuration with YAML
nav_order: 6
---
# Configuration with YAML

The entire configuration of the wiki can also be done through a `.yaml` file. 

All the customizations possible with environment variables, could be directly done editing the `wikmd-config.yaml` file.

Please, notice that if you set up both `wikmd-config.yaml` and environment variables, the `.yaml` file takes precedence.

## Configuration parameters

```yaml
wikmd_host: "0.0.0.0"
wikmd_port: 5000
wikmd_logging: 1
wikmd_logging_file: "wikmd.log"

sync_with_remote: 0
remote_url: ""
wiki_directory: "wiki"
images_route: "img"

homepage: "homepage.md"
homepage_title: "homepage"
```

Please, refer to [environment variables](environment%20variables.md) for further parameters explanation.