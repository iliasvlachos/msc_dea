# pull official base image
FROM python:3.9-slim-buster

# set workdir
WORKDIR /usr/src/app

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1


# install dependencies
RUN apt-get update \
    && apt-get -y install postgresql gcc

# set user:group
RUN groupadd appuser && useradd -g users -G appuser appuser  --home /usr/src/app

# change permission on workdir
RUN chown -R appuser:appuser /usr/src/app


USER appuser:appuser

ENV PATH=$PATH:/usr/src/app/.local/bin



# install requirements
RUN pip install --upgrade pip

COPY  --chown=appuser:appuser ./requirements.txt .

RUN pip install -r requirements.txt


#copy project
COPY  --chown=appuser:appuser dea_web .

RUN  python manage.py collectstatic --noinput

# TODO: superuser, migrations

WORKDIR /usr/src/app

ENTRYPOINT ["gunicorn", "--bind", "0.0.0.0:8000","dea.wsgi"]

