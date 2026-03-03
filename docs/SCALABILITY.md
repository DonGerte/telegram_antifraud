# Documentación de Escalado Horizontal

## Escalado con Redis Cluster

### Setup básico con Docker Compose

```yaml
version: '3.8'

services:
  redis-node-1:
    image: redis:7-alpine
    command: redis-server --cluster-enabled yes --cluster-node-timeout 5000 --port 6379
    ports:
      - "6379:6379"
    volumes:
      - redis1:/data

  redis-node-2:
    image: redis:7-alpine
    command: redis-server --cluster-enabled yes --cluster-node-timeout 5000 --port 6380
    ports:
      - "6380:6380"
    volumes:
      - redis2:/data

  redis-node-3:
    image: redis:7-alpine
    command: redis-server --cluster-enabled yes --cluster-node-timeout 5000 --port 6381
    ports:
      - "6381:6381"
    volumes:
      - redis3:/data

  # ... repeat for 3 sentinel nodes for HA

volumes:
  redis1:
  redis2:
  redis3:
```

### Crear el cluster

```bash
redis-cli --cluster create \
  localhost:6379 \
  localhost:6380 \
  localhost:6381 \
  --cluster-replicas 1
```

### Conectar múltiples workers

```python
# Por defecto, el worker se conecta a REDIS_URL
# Para usar cluster, configure:
export REDIS_URL=redis+cluster://localhost:6379/0

# O use Redis Sentinel para alta disponibilidad:
export REDIS_URL=redis-sentinel://localhost:26379/0/antifraud
```

---

## Escalado con Kafka

### Setup con Docker Compose

```yaml
services:
  zookeeper:
    image: confluentinc/cp-zookeeper:7.0.1
    environment:
      ZOOKEEPER_CLIENT_PORT: 2181

  kafka:
    image: confluentinc/cp-kafka:7.0.1
    depends_on:
      - zookeeper
    environment:
      KAFKA_BROKER_ID: 1
      KAFKA_ZOOKEEPER_CONNECT: zookeeper:2181
      KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://kafka:9092
      KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR: 3

  kafka-ui:
    image: provectuslabs/kafka-ui:latest
    ports:
      - "8080:8080"
    depends_on:
      - kafka
```

### Topics necesarios

```bash
kafka-topics --create \
  --bootstrap-server localhost:9092 \
  --topic data_bus \
  --partitions 12 \
  --replication-factor 3

kafka-topics --create \
  --bootstrap-server localhost:9092 \
  --topic action_bus \
  --partitions 6 \
  --replication-factor 3

kafka-topics --create \
  --bootstrap-server localhost:9092 \
  --topic signals \
  --partitions 24 \
  --replication-factor 3
```

### Configurar workers con Kafka

```python
# config.py
KAFKA_BOOTSTRAP = "localhost:9092"
USE_KAFKA = True  # toggle between Redis and Kafka
```

---

## Múltiples Workers Paralelos

### Con Docker Compose

```yaml
services:
  worker:
    image: antifraud:latest
    command: python engine/worker.py
    depends_on:
      - redis
    environment:
      REDIS_URL: redis://redis:6379/0
      WORKER_ID: ${WORKER_ID:-1}
    deploy:
      replicas: 4  # ejecutar 4 workers en paralelo
```

### Ejecutar manualmente

```bash
for i in {1..4}; do
  WORKER_ID=$i python engine/worker.py &
done
```

---

## Persistencia en PostgreSQL

### Escritura de eventos

El worker puede opcionalmente escribir signals/actions a PostgreSQL:

```python
# engine/worker.py
from db.models import Signal, ModAction, User, SessionLocal

def process_message(event):
    # ... existing logic ...
    db = SessionLocal()
    
    # Persist signal
    signal = Signal(
        user_id=user.id,
        signal_type=sig_type,
        value=value,
        chat_id=chat,
    )
    db.add(signal)
    
    # Persist action if needed
    if action_name != "none":
        action = ModAction(
            user_id=user.id,
            action=action_name,
            chat_id=chat,
            reason=reason,
            score_at_action=score,
        )
        db.add(action)
    
    db.commit()
    db.close()
```

---

## Monitoreo y Observabilidad

### Prometheus metrics

```python
from prometheus_client import Counter, Histogram, Gauge

# Métricas
messages_processed = Counter('messages_processed', 'Total messages')
processing_time = Histogram('processing_time_seconds', 'Processing time')
users_monitored = Gauge('users_monitored', 'Active monitored users')
actions_taken = Counter('actions_taken', 'Total actions', ['action_type'])
```

### Alertas Prometheus

```yaml
groups:
  - name: antifraud
    rules:
      - alert: HighMessageVolume
        expr: rate(messages_processed[5m]) > 1000
        annotations:
          summary: "High message volume detected"

      - alert: LowWorkerHealth
        expr: up{job="worker"} < 3
        annotations:
          summary: "Less than 3 workers running"
```

### Grafana Dashboards

Dashboard principal muestra:
- Throughput (msg/min, signals/min)
- Latencia de procesamiento
- Usuarios monitoreados (activos)
- Acciones por tipo (kicks, mutes, etc.)
- Tasa de falsos positivos
- Cobertura de raids detectados

---

## Consideraciones de escala

### Limites de Redis (single instance)

- **Max concurrencia**: ~10k connections
- **Throughput**: 50k-100k ops/sec
- **Memoria por user**: ~500 bytes (signals + cluster)
- **Max usuarios**: 10-50 millones con cluster

### Recomendaciones

| Escala | Broker | Workers | BD |
|--------|--------|---------|-----|
| < 1M eventos/día | Redis Simple | 1-2 | SQLite/None |
| 1M-10M | Redis Cluster | 4-8 | PostgreSQL |
| > 10M | Kafka | 16+ | PostgreSQL + TimescaleDB |

---

## Testing de carga

```bash
# Simular 100k eventos/hora
python tools/traffic_simulator.py --attack all \
  --duration 3600 --rate 28  # ~100k/hour
```
