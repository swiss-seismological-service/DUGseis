# Configuration

Before `DUGSeis` can be used, the setup of any given project must be
configured. It can be passed to the
{class}`~dug_seis.project.project.DUGSeisProject` class either as a dictionary
or as a YAML file.

This, additionally, is the configuration file passed to the graphical interface.

Here is an annotated example YAML file that explains the available options:

```{literalinclude} ../scripts/dug_seis_example.yaml
   :language: yaml
```