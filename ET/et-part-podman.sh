# podman build -t pdf-processor:1.1 ET
podman run -it --memory=4g --cpus=4.0 --rm localhost/et-proc:1.1 /bin/bash
