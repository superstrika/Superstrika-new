# Superstrika

## dependencies installation
1. First install apt dependencies:
```bash
sudo apt update
sudo apt install neovim build-essential swig python3-dev liblgpio-dev
```

2. If virtual environment wasn't created:
```bash
python3 -m venv venv
```

3. Enter the virtual environment:
```bash
source venv/bin/activate
```

4. Install the `requirements.txt`:
```bash
pip3 install -r requirements.txt
```