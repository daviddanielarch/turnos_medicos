terraform {
  required_providers {
    railway = {
      source  = "terraform-community-providers/railway"
      version = "0.5.2"
    }
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  backend "s3" {
    bucket  = "turnos-medicos-terraform-state"
    key     = "railway-infrastructure/terraform.tfstate"
    region  = "us-west-2"
    encrypt = true
  }
}
