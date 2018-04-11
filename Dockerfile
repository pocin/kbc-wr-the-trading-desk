FROM python:3.6-alpine
RUN pip3 install --no-cache-dir --upgrade \
      pytest \
      flake8 \
      requests \
      voluptuous \
      https://github.com/keboola/python-docker-application/tarball/master

WORKDIR /code

COPY . /code/

# Run the application
CMD python3 -u /code/main.py

