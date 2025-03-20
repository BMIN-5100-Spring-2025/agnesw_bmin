resource "aws_s3_bucket" "agnesw-project" {
  bucket = "agnesw-project"

  tags = {
    Owner = element(split("/", data.aws_caller_identity.current.arn), 1)
  }
}

resource "aws_s3_bucket_ownership_controls" "agnesw-project_ownership_controls" {
  bucket = aws_s3_bucket.agnesw-project.id
  rule {
    object_ownership = "BucketOwnerPreferred"
  }
}

resource "aws_s3_bucket_acl" "agnesw-project_acl" {
  depends_on = [aws_s3_bucket_ownership_controls.agnesw-project_ownership_controls]

  bucket = aws_s3_bucket.agnesw-project.id
  acl    = "private"
}

resource "aws_s3_bucket_lifecycle_configuration" "agnesw-project_expiration" {
  bucket = aws_s3_bucket.agnesw-project.id

  rule {
    id      = "compliance-retention-policy"
    status  = "Enabled"

    expiration {
	  days = 100
    }
  }
}