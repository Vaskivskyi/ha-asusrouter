## Documentation and tips

You can find the full documentation on the [official webpage](https://asusrouter.vaskivskyi.com/).

### Use HTTPS connection

It is recommended to use an HTTPS connection to your router (SSL). While both the SSL and non-SSL connections are fully supported, some devices might have issues with disconnects on HTTP. In order to use SSL, you need to enable it in the router settings: `Administration -> System -> Local Access Config -> Authentication Method`. Put it to `BOTH` (recommended) or `HTTPS`. Make note of the port number (default is `8443`).

### Connected devices number

The integration might show a different number of connected devices compared to the WebUI network map. In this case, refer to the number of devices shown in the `AiMesh` section of the WebUI. Those two are different regardless of the actual use of AiMesh.
