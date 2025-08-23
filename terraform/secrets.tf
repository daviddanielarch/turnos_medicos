# AWS Secrets Manager for sensitive data
resource "aws_secretsmanager_secret" "auth0_secret" {
  name        = "turnos-medicos/auth0-management-client-secret"
  description = "Auth0 Management Client Secret for Turnos Médicos"
}

resource "aws_secretsmanager_secret" "postgres_password" {
  name        = "turnos-medicos/postgres-password"
  description = "PostgreSQL password for Turnos Médicos"
}

# Data sources to fetch secrets
data "aws_secretsmanager_secret_version" "auth0_secret" {
  secret_id = aws_secretsmanager_secret.auth0_secret.id
}

data "aws_secretsmanager_secret_version" "postgres_password" {
  secret_id = aws_secretsmanager_secret.postgres_password.id
}
