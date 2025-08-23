resource "railway_service" "standalone_chrome" {
  name         = "standalone-chrome"
  project_id   = railway_project.allende-turnos.id
  source_image = "selenium/standalone-chrome:124.0"

  lifecycle {
    ignore_changes = [
      regions
    ]
  }
}
