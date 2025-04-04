# Telegram Bots Hub
**Telegram Bots Hub** is a microservice for managing Telegram bots within the [**Constructor Telegram Bots**](https://constructor.exg1o.org/) project.

## Requirements
- Linux
- Python 3.12.x

## Installing
To install, execute the following commands:
```bash
git clone https://github.com/EXG1O/Telegram-Bots-Hub.git
cd Telegram-Bots-Hub
git checkout $(git describe --tags --abbrev=0)
python -m venv env
source env/bin/activate
source install.sh
```

## Usage
To run, use the following command:
```bash
uvicorn main:app
```

## Contributing
Read [CONTRIBUTING.md](CONTRIBUTING.md) for more information on this.

## License
This repository is licensed under the [AGPL-3.0 License](LICENSE).
