resource "railway_service" "buscar_turnos" {
  name          = "Buscar turnos"
  project_id    = railway_project.allende-turnos.id
  cron_schedule = "*/5 * * * *"
  config_path   = "terraform/configs/buscar_turnos.json"

  lifecycle {
    ignore_changes = [
      regions
    ]
  }
}

resource "railway_variable" "buscar_turnos_vars" {
  for_each = {
    # Database Configuration
    "PGDATABASE" = "railway"
    "PGHOST"     = "postgres.railway.internal"
    "PGPORT"     = "5432"
    "PGUSER"     = "postgres"
    "PGPASSWORD" = data.aws_secretsmanager_secret_version.postgres_password.secret_string

    # Selenium Configuration
    "SELENIUM_HOSTNAME" = "standalone-chrome.railway.internal"
  }

  service_id     = railway_service.buscar_turnos.id
  environment_id = railway_environment.production.id
  name           = each.key
  value          = each.value
}
