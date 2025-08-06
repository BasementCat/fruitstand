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

## Running

Run the following commands to get up and running:

    npm install
    pipenv install
    docker compose up -d
    flask db upgrade
    flask run

## Building

To build assets for the main application, as well as any discovered screens:

    # prod
    flask run compile sass
    # dev/testing
    flask run compile sass --env dev --watch


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