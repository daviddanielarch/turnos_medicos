resource "railway_project" "allende-turnos" {
  name = "allende-turnos"
}

resource "railway_environment" "production" {
  name       = "production"
  project_id = railway_project.allende-turnos.id
}
