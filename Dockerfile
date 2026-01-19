# Alpine 3.2* has issues with timeouts in the provided version of chromium, see https://pptr.dev/troubleshooting#running-on-alpine
FROM alpine:3.19

# FROM alpine:3.22

EXPOSE 3031

RUN addgroup -S uwsgi && \
    adduser -S -G uwsgi uwsgi && \
    mkdir /app && \
    chown uwsgi:uwsgi /app
WORKDIR /app

RUN apk add --no-cache \
        uwsgi-python3 \
        python3 \
        py3-pip \
        npm \
        # required for puppeteer
        chromium \
        nss \
        freetype \
        harfbuzz \
        ca-certificates \
        ttf-freefont \
        dumb-init

# Tell Puppeteer to skip installing Chrome. We'll be using the installed package.
ENV PUPPETEER_EXECUTABLE_PATH=/usr/bin/chromium-browser

RUN pip3 config set global.break-system-packages true
RUN pip3 install pipenv

# TODO: install a version of node matching .nvmrc

COPY --chown=uwsgi package*.json ./
# Need to install js packages as user
USER uwsgi
RUN npm install --omit=dev
# And switch back to root for global python package install + running uWSGI (which drops permissions anyway)
USER root

COPY Pipfile* ./
RUN pipenv install --system --deploy

COPY . .
# RUN chown -R uwsgi:uwsgi /app
# RUN chmod -R 555 /app

# TODO: more fleshed out uwsgi configuration

ENTRYPOINT [ "/app/entrypoint.sh", \
               "--env", "HOME=/home/uwsgi", \
               "--uid", "uwsgi", \
               "--plugins", "python3", \
               "--wsgi", "wsgi:application" ]