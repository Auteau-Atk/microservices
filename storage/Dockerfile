FROM python:3.9
LABEL maintainer="hgelle@my.bcit.ca"

WORKDIR /app

COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app

RUN chown -R nobody:nogroup /app
USER nobody

EXPOSE 8090

ENTRYPOINT ["python"]
CMD ["app.py"]
