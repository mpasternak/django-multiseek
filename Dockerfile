FROM mpasternak79/docker-builder

EXPOSE 9015

RUN mkdir -p /usr/src/app
WORKDIR /usr/src/app
COPY . /usr/src/app

RUN pip install -U tox pip

COPY .docker/pytest.ini . 

ENTRYPOINT ["./entrypoint.sh"]
