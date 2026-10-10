resource "railway_service" "frontend" {
  name       = "turnos-medicos-web"
  project_id = railway_project.allende-turnos.id
  # Deployed with `railway up mobile/allende --path-as-root`, which picks up mobile/allende/railway.json

  lifecycle {
    ignore_changes = [
      regions
    ]
  }
}

resource "railway_service_domain" "frontend" {
  subdomain      = "turnos-medicos-web"
  service_id     = railway_service.frontend.id
  environment_id = railway_environment.production.id
}

resource "railway_variable" "frontend_vars" {
  for_each = {
    # Inlined into the web bundle at build time
    "EXPO_PUBLIC_API_HOST" = "https://turnos-medicos.up.railway.app"
  }

  service_id     = railway_service.frontend.id
  environment_id = railway_environment.production.id
  name           = each.key
  value          = each.value
}

output "frontend_url" {
  value = "https://${railway_service_domain.frontend.domain}"
}
