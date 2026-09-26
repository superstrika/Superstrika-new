# Runtime environment for the robot. The code itself is bind-mounted at /robot
# by docker-compose, so this image only needs rebuilding when dependencies change.
ARG DEBIAN_RELEASE=trixie
FROM debian:${DEBIAN_RELEASE}-slim
ARG DEBIAN_RELEASE

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/robot \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Raspberry Pi apt repo: libcamera/picamera2 and lgpio are not usable from pip.
# The legacy raspberrypi.gpg.key has SHA1 self-signatures that trixie's apt (sqv)
# rejects, so install the same keyring package Pi OS ships, pinned by checksum.
ARG RPI_KEYRING_DEB=raspberrypi-archive-keyring_2025.1+rpt1_all.deb
ARG RPI_KEYRING_SHA256=2e727149d7acb8cc7f604e66d0049161039c8aa1eaf1175e54f9e69d963d60e4
RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates curl \
    && curl -fsSL -o /tmp/rpi-keyring.deb \
        "https://archive.raspberrypi.com/debian/pool/main/r/raspberrypi-archive-keyring/${RPI_KEYRING_DEB}" \
    && echo "${RPI_KEYRING_SHA256}  /tmp/rpi-keyring.deb" | sha256sum -c - \
    && dpkg -i /tmp/rpi-keyring.deb && rm /tmp/rpi-keyring.deb \
    && echo "deb [signed-by=/usr/share/keyrings/raspberrypi-archive-keyring.pgp] http://archive.raspberrypi.com/debian ${DEBIAN_RELEASE} main" \
        > /etc/apt/sources.list.d/raspi.list \
    && apt-get update && apt-get install -y --no-install-recommends \
        python3 \
        python3-venv \
        python3-pip \
        python3-picamera2 \
        python3-lgpio \
        python3-numpy \
        i2c-tools \
        v4l-utils \
        libusb-1.0-0 \
        libgl1 \
        libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# venv sees the apt packages (picamera2, lgpio, numpy) and adds the pip ones on top
RUN python3 -m venv --system-site-packages /opt/venv
ENV PATH=/opt/venv/bin:$PATH

COPY robot/requirements.txt constraints.txt /tmp/
RUN pip install --no-cache-dir -r /tmp/requirements.txt -c /tmp/constraints.txt

WORKDIR /robot
COPY . .

CMD ["python3", "main.py"]
