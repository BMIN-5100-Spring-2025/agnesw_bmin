terraform {
  backend "s3" {
    bucket         = "bmin5100-terraform-state"
    key            = "agnesw@seas.upenn.edu-FDAscope/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
  }
}