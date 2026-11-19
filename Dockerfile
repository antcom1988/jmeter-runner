FROM alpine/jmeter:latest

# JMeter executes tests; Flask provides the local, no-auth control dashboard.
RUN apk add --no-cache python3 py3-flask

WORKDIR /app
COPY webapp /app/webapp

ENV WORKSPACE=/srv \
    PYTHONUNBUFFERED=1

VOLUME ["/srv"]
EXPOSE 8080

# The base image defines a JMeter entrypoint; reset it so this is a web server.
ENTRYPOINT []
CMD ["python3", "-m", "webapp.app"]
