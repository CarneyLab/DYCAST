FROM python:3.7.4

RUN apt-get update -y &&\
	apt-get upgrade -y &&\
	apt-get install -y dos2unix

## Install Postgresql client
RUN echo "deb http://apt.postgresql.org/pub/repos/apt/ trusty-pgdg main" >> /etc/apt/sources.list.d/pgdg.list &&\
	wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | apt-key add - &&\
	apt-get update -y &&\
	apt-get install -y postgresql-client-9.6 postgresql-9.6-postgis-2.2

ENV DYCAST_PATH=/dycast
ENV DYCAST_APP_PATH=${DYCAST_PATH}/application
ENV DYCAST_REQUIREMENTS_PATH=${DYCAST_APP_PATH}/init/requirements.txt
ENV PG_SHARE_PATH=/usr/local/pgsql/share
ENV DOCKER_DIR=/docker
ENV PYTHONPATH=${DYCAST_PATH}:$PYTHONPATH

# First only copy the requirements file, so the build can be cached beyond the `pip install` part
ADD ./application/init/requirements.txt ${DYCAST_REQUIREMENTS_PATH}
RUN pip install -r ${DYCAST_REQUIREMENTS_PATH}

COPY ./application ${DYCAST_APP_PATH}

# Tests cannot be executable
RUN chmod -R -x ${DYCAST_APP_PATH}/tests

COPY docker/entrypoint.sh ${DOCKER_DIR}/entrypoint.sh
RUN	chmod -R 700 ${DOCKER_DIR} &&\
	dos2unix ${DOCKER_DIR}/*

WORKDIR ${DYCAST_APP_PATH}

# Set entrypoint
ENTRYPOINT ["/docker/entrypoint.sh"]
CMD ["run_dycast"]