FROM alpine:3.22

EXPOSE 3031
WORKDIR /app

RUN apk add --no-cache \
        uwsgi-python3 \
        python3 \
        py3-pip \
        npm
RUN pip3 config set global.break-system-packages true
RUN pip3 install pipenv

# TODO: install a version of node matching .nvmrc

COPY package*.json ./
RUN npm install --omit=dev

COPY Pipfile* ./
RUN pipenv install --system --deploy

COPY . .

# TODO: more fleshed out uwsgi configuration

ENTRYPOINT [ "uwsgi", "--socket", "0.0.0.0:3031", \
               "--uid", "uwsgi", \
               "--plugins", "python3", \
               "--protocol", "uwsgi", \
               "--wsgi", "wsgi:application" ]