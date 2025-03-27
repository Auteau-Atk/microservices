FROM python:3.9
LABEL maintainer="hgelle@my.bcit.ca"

WORKDIR /app

COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app

# Ensure the directory and file are owned by nobody
RUN mkdir -p /app/stats && \
    touch /app/stats/stats.json && \
    chown -R nobody:nogroup /app/stats

USER nobody

EXPOSE 8100

ENTRYPOINT ["python"]
CMD ["app.py"]

