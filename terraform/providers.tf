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
}

provider "railway" {
  # Configuration options
}

provider "aws" {
  region = "us-west-2" # Change this to your preferred AWS region
}
