# Fruitstand

Simple digital signage, inspired by https://usetrmnl.com/ and https://www.hackster.io/lmarzen/esp32-e-paper-weather-display-a2f444

## Development:

### Required Software

* Install PipEnv
* Install NVM or use your method of choice to install the version of node in ".nvmrc"
* Install Docker, or otherwise install MySQL/MariaDB and Redis (optional)
    * Alternatively, other SQL servers like PostgreSQL/SQLite may work but are untested

### Configuration

Create a .env file with at least the following keys:

    FLASK_SECRET_KEY=lkasdjfalsdkjflskjdklsjdflk
    FLASK_SQLALCHEMY_DATABASE_URI=mysql+pymysql://fruitstand:password@localhost:3306/fruitstand

## Running

Run the following commands to get up and running:

    npm install
    pipenv install
    docker compose up -d
    flask db migrate
    flask run