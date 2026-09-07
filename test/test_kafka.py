from confluent_kafka.admin import AdminClient


KAFKA_BOOTSTRAP_SERVERS = (
    "10.62.7.43:9192,"
    "10.62.7.44:9192,"
    "10.62.7.45:9192"
)


admin = AdminClient({
    "bootstrap.servers": KAFKA_BOOTSTRAP_SERVERS,
    "security.protocol": "PLAINTEXT",

    "api.version.request": False,
    "broker.version.fallback": "2.3.0",

    "socket.timeout.ms": 10000,
    "request.timeout.ms": 10000,

    "debug": "broker,protocol",
})


print("Testing Kafka connection...")

metadata = admin.list_topics(timeout=10)

print("Kafka connected!")
print("Cluster ID:", metadata.cluster_id)