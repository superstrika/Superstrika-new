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

# Raspberry Pi apt repo: libcamera/picamera2 and lgpio are not usable from pip
RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates curl gnupg \
    && curl -fsSL https://archive.raspberrypi.com/debian/raspberrypi.gpg.key \
        | gpg --dearmor -o /usr/share/keyrings/raspberrypi.gpg \
    && echo "deb [signed-by=/usr/share/keyrings/raspberrypi.gpg] http://archive.raspberrypi.com/debian ${DEBIAN_RELEASE} main" \
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
