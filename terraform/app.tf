resource "railway_service" "app" {
  name        = "turnos-medicos"
  project_id  = railway_project.allende-turnos.id
  config_path = "configs/turnos_medicos.json"

  lifecycle {
    ignore_changes = [
      regions
    ]
  }
}

resource "railway_variable" "app_vars" {
  for_each = {
    # Auth0 Configuration
    "AUTH0_CLIENT_ID"                = "8IYHXBrV3fqEEfFsupCZNfXc8ikTS8CB"
    "AUTH0_MANAGEMENT_CLIENT_ID"     = "moEtqx1MjnV429odXtz4gDU32PtYnugq"
    "AUTH0_MANAGEMENT_CLIENT_SECRET" = data.aws_secretsmanager_secret_version.auth0_secret.secret_string

    # Database Configuration
    "PGDATABASE" = "railway"
    "PGHOST"     = "postgres.railway.internal"
    "PGPORT"     = "5432"
    "PGUSER"     = "postgres"
    "PGPASSWORD" = data.aws_secretsmanager_secret_version.postgres_password.secret_string

    # Selenium Configuration
    "SELENIUM_HOSTNAME" = "standalone-chrome.railway.internal"
  }

  service_id     = railway_service.app.id
  environment_id = railway_environment.production.id
  name           = each.key
  value          = each.value
}
