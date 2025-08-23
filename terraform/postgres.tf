resource "railway_service" "postgres" {
  name         = "Postgres"
  project_id   = railway_project.allende-turnos.id
  source_image = "ghcr.io/railwayapp-templates/postgres-ssl:16"

  regions = [
    {
      num_replicas = 1
      region       = "us-west2"
    },
  ]

  volume = {
    mount_path = "/var/lib/postgresql/data"
    name       = "abundant-volume"
  }

  lifecycle {
    ignore_changes = [regions]
  }
}
