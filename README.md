  docker compose --env-file docker-compose.env up -d
  docker exec postgres_db psql -U postgres -d photography_studio -c "\dt studio.*"