FROM python:3.11-slim

# update os
RUN apt-get update && apt-get install -y

# add curl
RUN apt-get install -y curl

# update pip
RUN pip install --upgrade pip

# set workdir
WORKDIR app/

# install poetry
RUN curl -sSL https://install.python-poetry.org | python -

# updating PATH
ENV PATH="${PATH}:/root/.local/bin"
ENV PYTHONPATH="/app/"

# copy source and requirement files
COPY . .

# disable creating venv
RUN poetry config virtualenvs.create false

# install requirements
RUN poetry install

# run uvicorn
CMD python manage.py migrate && \
    uvicorn psudilku.asgi:application --host 0.0.0.0 --port 8000 --reload
