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

    FRUITSTAND_SECRET_KEY=lkasdjfalsdkjflskjdklsjdflk
    FRUITSTAND_SQLALCHEMY_DATABASE_URI=mysql+pymysql://fruitstand:password@localhost:3306/fruitstand

Configuration may also be passed by setting environment variables.  All supported flask configuration from https://flask.palletsprojects.com/en/stable/config/ are supported (use the prefix FRUITSTAND instead of FLASK).  In addition, the following config options are understood:

* **FRUITSTAND_SCREEN_IMPORTS** - A comma-separated list of modules to import that contain screen definitions
* **FRUITSTAND_TIMEZONE** - Default timezone for the installation
* **FRUITSTAND_CACHE_DRIVER** - Cache driver to use, valid options are:
    * `filesystem` (default)
    * `database`
* **FRUITSTAND_FILESYSTEM_CACHE_DIR** - For filesystem caching, the directory to store data. Must exist.
* **FRUITSTAND_FILESYSTEM_CACHE_SUBDIR** - Subdirectory within the system temp dir to store data, optional.  Does not need to already exist.
* **FRUITSTAND_BROWSER** - Browser to use for rendering, "firefox" or "chrome" (must be installed via `npx puppeteer browsers install <browser>`)
  * NOTE: chrome is installed & used by default, and allows for the ability to (more or less) completely disable antialiasing (fonts & SVGs)/subpixel font rendering - Firefox does not, and so is not recommended for smaller monochrome displays
* **FRUITSTAND_INTERNAL_WEB_HOST** - Internal host for web requests.
  * For a production deployment, setting the default SERVER_NAME is fine as it should be resolvable.
  * For local development with Docker, "localhost" likely won't work as this most likely will be in a container running uWSGI, so point to the actual front proxy container name.
* **FRUITSTAND_ENABLE_USERS** - Enable user management & login.
  * If not set, user functionality will be unavailable and any visitor can manage everything.
  * It's highly recommended to enable this if hosting Fruitstand outside of a local network.
* **FRUITSTAND_ENABLE_DISPLAY_APPROVAL** - Enable display approval.
  * When enabled, any new screens require approval before they will display any content.
* **FRUITSTAND_ENABLE_DISPLAY_AUTH** - Enable display authentication
  * When enabled, screens must provide a valid secret key (via the `sk` parameter) before they will display any content.
* **FRUITSTAND_NO_AUTO_MIGRATE** - Do not automatically run migrations
  * This is not used directly by the Flask app, but rather by the entrypoint script
  * By default, the entrypoint script will attempt to run migrations prior to starting the app
  * In a case where you have many containers you probably don't want all of them doing this, or if you prefer to run them manually

## Running

### Docker

#### For Development

A Dockerfile + compose file are provided for easy setup, running the application via uWSGI on HTTP port 8000.  To start, run `docker compose up -d`.  This starts the necessary services, and a locally-built app container running several processes that will automatically reload when Python code is changed.

#### For Development - Latest Version

An additional compose file is provided that runs the latest version of the pre-built image with a slightly more robust uWSGI configuration, and does not mount the local repository into the image (and thus won't auto-reload code or reflect changes to the local repository).  To start, run `docker compose -f docker-compose.yaml -f docker-compose-prod.yaml up -d`.

#### For Production

For a completely custom Docker setup, use one of the following images:

  * `ghcr.io/basementcat/fruitstand:latest` - Latest tagged version
  * `ghcr.io/basementcat/fruitstand:master` - Latest master branch
  * `ghcr.io/basementcat/fruitstand:develop` - Development branch, likely to be ahead of latest/master, may be broken.

The container can be configured using the environment variables above, or a `.env` file if present.  As above, the application will run on HTTP port 8000 with a minimal uWSGI configuration; you will have to supply any additional configuration as an alternative command or replace the entryoint if you want a different protocol like WSGI.

This approach is recommended for a "real" (i.e. non-development) deployment, as it avoids using the default database passwords and allows for the most flexibility in configuration.

#### Database Migrations

The entrypoint script automatically waits for the database to be ready, and then runs database migrations.  If this behavior is not desired, it can be disabled by setting the environment variable `FRUITSTAND_NO_AUTO_MIGRATE=1` (any non-empty value is acceptable), in which case migrations must be run manually with `docker compose exec app -- flask db upgrade`.

### Local development environment

In order to run locally you'll need to set up a minimal configuration as explained above, either in a `.env` file or by setting environment variables.  Run the following commands to get up and running:

    npm install
    pipenv install
    docker compose up -d
    flask db upgrade
    flask run

When pulling a new version, database migrations may be required - run `flask db upgrade` again to apply them if any new migrations are present.

## Building

To build assets for the main application, as well as any discovered screens:

    # prod
    flask compile sass
    # dev/testing
    flask compile sass --env dev --watch

To build within Docker if you do not set up a local development environment, prefix the commands with `docker compose exec app --`, for example `docker compose exec app -- flask compile sass`

## Sources/Attributions

Heavily inspired by:

* https://github.com/lmarzen/esp32-weather-epd/tree/main
* https://usetrmnl.com/

Icons from:

********************************************************************************
.svg files prefixed with 'wi-' ('wi-**.svg') in the sub-directory 'svg'
  Retrieved from: https://github.com/erikflowers/weather-icons
  Weather Icons licensed under SIL OFL 1.1: http://scripts.sil.org/OFL
  Code licensed under MIT License: http://opensource.org/licenses/mit-license.html
  Documentation licensed under CC BY 3.0: http://creativecommons.org/licenses/by/3.0
********************************************************************************

********************************************************************************
.svg files prefixed with 'battery' (battery**.svg) in the sub-directory 'svg'
Visibility Icon 'visibility_icon.svg' in the sub-directory 'svg'
  Retrieved from: https://fonts.google.com/icons
  Licensed under Apache License, Version 2.0: https://www.apache.org/licenses/LICENSE-2.0.txt
********************************************************************************

********************************************************************************
House Icon 'house.svg' in the sub-directory 'svg'
  Retrieved from: https://seekicon.com/free-icon/house_16
  Licensed under MIT License: http://opensource.org/licenses/mit-license.html
********************************************************************************

********************************************************************************
.svg files prefixed with 'wifi' (wifi**.svg) in the sub-directory 'svg'
Warning Alert Icon 'warning_icon.svg' in the sub-directory 'svg'
Warning Alert Icon 'error_icon.svg' in the sub-directory 'svg'
  Retrieved from: https://github.com/phosphor-icons/homepage
  Licensed under MIT License: http://opensource.org/licenses/mit-license.html
********************************************************************************

********************************************************************************
House Icon 'house.svg' in the sub-directory 'svg'
  Retrieved from: https://seekicon.com/free-icon/house_16
  Licensed under MIT License: http://opensource.org/licenses/mit-license.html

'house_temperature.svg', 'house_humidity.svg', and 'house_rainsdrops.svg' were
created by transforming icons from https://github.com/erikflowers/weather-icons
with 'house.svg' and as such are
  Licensed under SIL OFL 1.1: http://scripts.sil.org/OFL
********************************************************************************

********************************************************************************
'ionizing_radiation_symbol.svg' in the sub-directory 'svg'
  Retrieved from: https://svgsilh.com/image/309911.html
  Licensed under CC0 1.0: https://creativecommons.org/publicdomain/zero/1.0/
********************************************************************************

********************************************************************************
'biological_hazard_symbol.svg' in the sub-directory 'svg'
  Retrieved from: https://svgsilh.com/image/37775.html
  Licensed under CC0 1.0: https://creativecommons.org/publicdomain/zero/1.0/
********************************************************************************

********************************************************************************
Wind Direction Icons 'meteorological_wind_direction_**deg.svg' in the
sub-directory 'svg'
  Retrieved from: https://www.onlinewebfonts.com/icon/251550
  Licensed under CC BY 3.0: http://creativecommons.org/licenses/by/3.0
********************************************************************************