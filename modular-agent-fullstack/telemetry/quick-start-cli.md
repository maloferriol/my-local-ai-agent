# Doc

## Docker Compose

### Useful commands

To start all services in detached mode

```lang=shell
docker-compose up -d
```

To take them down

```lang=shell
docker-compose down
```

To view logs

```lang=shell
docker-compose logs -f <service_name>
```

To stop individual services

```lang=shell
docker-compose stop <service_name>
```

To start individual services

```lang=shell
docker-compose start <service_name>
```

To remove individual services

```lang=shell
docker-compose rm -f <service_name>
```

To inspect the config of the current docker running

```lang=shell
docker-compose config
```
